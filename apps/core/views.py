"""
Generic CRUD engine + dashboard + custom-field management.

`record_list/create/edit/delete` are driven entirely by `registry.MODULES`, so
every module gets consistent list/search/filter/create/edit/delete behaviour and
teacher-scoping for free. Special-case detail screens live in their domain apps.
"""

from django.contrib.auth.decorators import login_required
from django.db.models import Max, Q
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from apps.accounts.services import create_student_account
from apps.cohorts.models import Cohort, Curriculum
from apps.leads.models import Lead

from . import permissions as perm
from . import selectors
from .custom_fields import inject_custom_fields
from .decorators import admin_required
from .forms import FieldDefinitionForm
from .models import FieldDefinition
from .registry import YES_NO_CHOICES, get_module


# --------------------------------------------------------------------------- #
# Dashboard
# --------------------------------------------------------------------------- #
@login_required
def dashboard(request):
    role = perm.role_of(request.user)
    if role == "student":
        return redirect("portal_home")
    is_teacher = role == "teacher"
    context = selectors.dashboard_context(request.user, is_teacher)
    context.update({"is_teacher": is_teacher, "can_score_any": role in ("admin", "teacher")})
    return render(request, "dashboard.html", context)


# --------------------------------------------------------------------------- #
# Generic list / create / edit / delete
# --------------------------------------------------------------------------- #
def _resolve(obj, path):
    val = obj
    for part in path.split("."):
        if val is None:
            return None
        val = getattr(val, part, None)
        if callable(val):
            val = val()
    return val


def _bool_param(value):
    return value == "yes"


_PARENT_DETAIL_URL_NAMES = {Lead: "lead_detail", Cohort: "cohort_detail", Curriculum: "curriculum_detail"}


def _back_url(cfg, request, obj):
    next_url = request.POST.get("next") or request.GET.get("next")
    if next_url:
        return next_url
    if cfg.get("parent_field"):
        parent = getattr(obj, cfg["parent_field"], None)
        detail_name = _PARENT_DETAIL_URL_NAMES.get(type(parent))
        if parent is not None and detail_name:
            return reverse(detail_name, args=[parent.pk])
    return reverse("record_list", args=[cfg["key"]])


@login_required
def record_list(request, module_key):
    cfg = get_module(module_key)
    if not perm.can_view(request.user, module_key):
        return HttpResponseForbidden("You don't have access to this section.")
    qs = perm.scope_queryset(request.user, module_key, cfg["model"].objects.all())

    parent_id = request.GET.get(cfg.get("parent_field", "__none__"))
    parent_obj = None
    if cfg.get("parent_field") and parent_id:
        qs = qs.filter(**{cfg["parent_field"] + "_id": parent_id})
        parent_obj = get_object_or_404(cfg["parent_model"], pk=parent_id)

    q = request.GET.get("q", "").strip()
    if q and cfg.get("search_fields"):
        query = Q()
        for f in cfg["search_fields"]:
            query |= Q(**{f + "__icontains": q})
        qs = qs.filter(query)

    filter_defs = []
    computed_filters = []
    active_filter_count = 0
    for f in cfg.get("filters", []):
        choices = f["choices"] if "choices" in f else f["choices_fn"]()
        value = request.GET.get(f["param"], "").strip()
        if value:
            active_filter_count += 1
        filter_defs.append({"param": f["param"], "label": f["label"], "choices": choices, "value": value})
        if not value:
            continue
        is_yes_no = choices == YES_NO_CHOICES
        if f.get("computed"):
            computed_filters.append((f["computed"], _bool_param(value) if is_yes_no else value, is_yes_no))
        elif is_yes_no:
            qs = qs.filter(**{f["field"]: _bool_param(value)})
        else:
            qs = qs.filter(**{f["field"]: value})

    objects = list(qs[:1000])
    for attr, expected, is_yes_no in computed_filters:
        if is_yes_no:
            objects = [o for o in objects if bool(getattr(o, attr)) == expected]
        else:
            objects = [o for o in objects if str(getattr(o, attr)) == str(expected)]
    objects = objects[:500]

    rows = [
        {"obj": obj, "cells": [{"value": _resolve(obj, path), "badge": badge} for _, path, badge in cfg["list_columns"]]}
        for obj in objects
    ]

    extra_context = {}
    if module_key == "followups":
        # Build the flagged card from the full (unfiltered) scoped set so it stays
        # stable regardless of the current search/filter. Admissions sources
        # (call status) only for roles that can see leads.
        scoped = perm.scope_queryset(request.user, module_key, cfg["model"].objects.all())
        include_admissions = perm.role_of(request.user) != "teacher"
        extra_context["flagged_items"] = selectors.flagged_attention_items(scoped, include_admissions)

    return render(
        request,
        "generic/list.html",
        {
            "cfg": cfg,
            "rows": rows,
            "q": q,
            "parent_obj": parent_obj,
            "module_key": module_key,
            "filter_defs": filter_defs,
            "active_filter_count": active_filter_count,
            "can_edit": perm.can_edit(request.user, module_key),
            **extra_context,
        },
    )


@login_required
def record_create(request, module_key):
    cfg = get_module(module_key)
    if not perm.can_edit(request.user, module_key):
        return HttpResponseForbidden("You don't have permission to add records here.")
    FormClass = inject_custom_fields(cfg["form"], cfg["target_model"]) if cfg.get("target_model") else cfg["form"]

    initial = {}
    parent_id = request.GET.get(cfg.get("parent_field", "__none__"))
    if cfg.get("parent_field") and parent_id:
        initial[cfg["parent_field"]] = parent_id
    if module_key == "class-events" and parent_id:
        cohort = get_object_or_404(Cohort, pk=parent_id)
        if cohort.class_time:
            initial["time"] = cohort.class_time
    lead_id = request.GET.get("lead")
    if lead_id and "lead" in [f.name for f in cfg["model"]._meta.get_fields()]:
        initial["lead"] = lead_id

    if request.method == "POST":
        form = FormClass(request.POST, initial=initial)
        if form.is_valid():
            obj = form.save(commit=False)
            if not perm.owns_object(request.user, module_key, obj):
                return HttpResponseForbidden("You can only add records under your own cohorts.")
            if module_key in ("followups", "class-events"):
                obj.created_by = request.user
            obj.save()
            if hasattr(form, "save_m2m"):
                form.save_m2m()
            if module_key == "leads" and not obj.student_account_id:
                create_student_account(obj)
            return redirect(_back_url(cfg, request, obj))
    else:
        form = FormClass(initial=initial)

    return render(request, "generic/form.html", {"cfg": cfg, "form": form, "is_new": True, "module_key": module_key})


@login_required
def record_edit(request, module_key, pk):
    cfg = get_module(module_key)
    obj = get_object_or_404(cfg["model"], pk=pk)
    if not perm.can_edit(request.user, module_key) or not perm.owns_object(request.user, module_key, obj):
        return HttpResponseForbidden("You don't have permission to edit this record.")
    FormClass = inject_custom_fields(cfg["form"], cfg["target_model"]) if cfg.get("target_model") else cfg["form"]

    if request.method == "POST":
        form = FormClass(request.POST, instance=obj)
        if form.is_valid():
            new_obj = form.save(commit=False)
            if not perm.owns_object(request.user, module_key, new_obj):
                return HttpResponseForbidden("You can't move this record outside your own cohorts.")
            new_obj.save()
            if hasattr(form, "save_m2m"):
                form.save_m2m()
            return redirect(_back_url(cfg, request, obj))
    else:
        form = FormClass(instance=obj)

    return render(request, "generic/form.html", {"cfg": cfg, "form": form, "is_new": False, "obj": obj, "module_key": module_key})


@login_required
def record_delete(request, module_key, pk):
    cfg = get_module(module_key)
    obj = get_object_or_404(cfg["model"], pk=pk)
    if not perm.can_edit(request.user, module_key) or not perm.owns_object(request.user, module_key, obj):
        return HttpResponseForbidden("You don't have permission to delete this record.")
    back = _back_url(cfg, request, obj)
    if request.method == "POST":
        obj.delete()
        return redirect(back)
    return render(request, "generic/confirm_delete.html", {"cfg": cfg, "obj": obj, "module_key": module_key})


# --------------------------------------------------------------------------- #
# Custom field management (Admin only)
# --------------------------------------------------------------------------- #
@admin_required
def manage_fields(request, target_model=None):
    target_model = target_model or FieldDefinition.TargetModel.LEAD
    fields = FieldDefinition.objects.filter(target_model=target_model)
    return render(
        request,
        "fields/manage_fields.html",
        {"fields": fields, "target_model": target_model, "target_choices": FieldDefinition.TargetModel.choices},
    )


@admin_required
def field_create(request, target_model):
    if request.method == "POST":
        form = FieldDefinitionForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("manage_fields", target_model=target_model)
    else:
        max_order = FieldDefinition.objects.filter(target_model=target_model).aggregate(Max("order"))["order__max"] or 0
        form = FieldDefinitionForm(initial={"target_model": target_model, "order": max_order + 1})
    return render(request, "fields/field_form.html", {"form": form, "target_model": target_model, "is_new": True})


@admin_required
def field_edit(request, pk):
    obj = get_object_or_404(FieldDefinition, pk=pk)
    if request.method == "POST":
        form = FieldDefinitionForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            return redirect("manage_fields", target_model=obj.target_model)
    else:
        form = FieldDefinitionForm(instance=obj)
    return render(request, "fields/field_form.html", {"form": form, "target_model": obj.target_model, "is_new": False, "obj": obj})


@admin_required
def field_delete(request, pk):
    obj = get_object_or_404(FieldDefinition, pk=pk)
    target_model = obj.target_model
    if request.method == "POST":
        obj.delete()
        return redirect("manage_fields", target_model=target_model)
    return render(request, "fields/field_confirm_delete.html", {"obj": obj})


@admin_required
def field_move(request, pk, direction):
    obj = get_object_or_404(FieldDefinition, pk=pk)
    siblings = list(FieldDefinition.objects.filter(target_model=obj.target_model).order_by("order", "id"))
    idx = siblings.index(obj)
    swap_idx = idx - 1 if direction == "up" else idx + 1
    if 0 <= swap_idx < len(siblings):
        other = siblings[swap_idx]
        obj.order, other.order = other.order, obj.order
        obj.save(update_fields=["order"])
        other.save(update_fields=["order"])
    return redirect("manage_fields", target_model=obj.target_model)
