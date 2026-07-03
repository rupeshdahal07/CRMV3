"""Lead detail + the admissions actions that hang off it."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import User
from apps.accounts.services import create_student_account, set_student_credentials
from apps.cohorts.forms import FollowupForm
from apps.cohorts.models import DailyScore, Followup
from apps.consultations.models import Consultation, ConsultationSlot
from apps.core import permissions as perm

from .models import DOCUMENTATION_STATUS_CHOICES, Lead
from .selectors import build_followup_history, build_lead_notes, build_lead_timeline


@login_required
def lead_detail(request, pk):
    if perm.role_of(request.user) == "teacher":
        return HttpResponseForbidden("Admissions records aren't available to Teachers.")
    lead = get_object_or_404(Lead, pk=pk)
    already_reserved_slot_ids = lead.consultations.values_list("slot_id", flat=True)
    open_slot_count = (
        ConsultationSlot.objects.filter(status__in=["Open", "Reserved"])
        .exclude(id__in=already_reserved_slot_ids)
        .count()
    )
    already_enrolled_cohort_ids = set(lead.enrollments.values_list("cohort_id", flat=True))
    enroll_suggestion = (
        lead.post_consultation_calls.filter(cohort_interest=True, preferred_cohort__isnull=False)
        .exclude(preferred_cohort_id__in=already_enrolled_cohort_ids)
        .exclude(preferred_cohort__status="Finished")
        .select_related("preferred_cohort")
        .order_by("-call_date")
        .first()
    )
    return render(
        request,
        "leads/lead_detail.html",
        {
            "lead": lead,
            "consultations": lead.consultations.select_related("slot", "slot__counselor").all(),
            "post_calls": lead.post_consultation_calls.select_related("called_by", "preferred_cohort").all(),
            "enrollments": lead.enrollments.select_related("cohort").all(),
            "followups": lead.followups.all(),
            "timeline": build_lead_timeline(lead),
            "notes": build_lead_notes(lead),
            "followup_history": build_followup_history(lead),
            "stages": Lead.STAGES,
            "stage_index": lead.stage_index,
            "current_stage": lead.current_stage,
            "open_slot_count": open_slot_count,
            "enroll_suggestion": enroll_suggestion,
            "documentation_status_choices": DOCUMENTATION_STATUS_CHOICES,
        },
    )


@login_required
def lead_student_credentials(request, pk):
    lead = get_object_or_404(Lead, pk=pk)
    role = perm.role_of(request.user)
    if role not in ("admin", "support", "teacher"):
        return HttpResponseForbidden("You don't have permission to view student login details.")
    if role == "teacher" and not lead.enrollments.filter(cohort__assigned_teacher=request.user).exists():
        return HttpResponseForbidden("You can only view login details for your own cohort's students.")

    account = lead.student_account or create_student_account(lead)

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "").strip()
        if username and User.objects.filter(username=username).exclude(pk=account.pk).exists():
            messages.error(request, "That username is already taken.")
        else:
            set_student_credentials(account, username=username or None, password=password or None)
            messages.success(request, "Student login updated.")
            return redirect("lead_student_credentials", pk=lead.pk)

    return render(request, "leads/lead_student_credentials.html", {"lead": lead, "account": account})


@login_required
def lead_mark_ready(request, pk):
    if perm.role_of(request.user) not in ("admin", "support"):
        return HttpResponseForbidden("Only Admins/Support can update this.")
    lead = get_object_or_404(Lead, pk=pk)
    if request.method == "POST":
        lead.ready_for_consultation = not lead.ready_for_consultation
        lead.save(update_fields=["ready_for_consultation"])
    return redirect("lead_detail", pk=lead.pk)


@login_required
def lead_update_documentation_status(request, pk):
    if perm.role_of(request.user) not in ("admin", "support"):
        return HttpResponseForbidden("Only Admins/Support can update this.")
    lead = get_object_or_404(Lead, pk=pk)
    if request.method == "POST":
        value = request.POST.get("documentation_status", "")
        valid_values = {choice for choice, _ in Lead._meta.get_field("documentation_status").choices} | {""}
        if value in valid_values:
            lead.documentation_status = value
            lead.save(update_fields=["documentation_status"])
    return redirect("lead_detail", pk=lead.pk)


@login_required
def lead_reserve_slot(request, pk):
    if perm.role_of(request.user) not in ("admin", "support"):
        return HttpResponseForbidden("Only Admins/Support can reserve slots.")
    lead = get_object_or_404(Lead, pk=pk)
    already_reserved_slot_ids = lead.consultations.values_list("slot_id", flat=True)
    open_slots = (
        ConsultationSlot.objects.filter(status__in=["Open", "Reserved"])
        .exclude(id__in=already_reserved_slot_ids)
        .select_related("counselor")
        .order_by("date", "time")
    )
    return render(request, "leads/lead_reserve_slot.html", {"lead": lead, "open_slots": open_slots})


@login_required
def lead_reserve_slot_confirm(request, pk, slot_pk):
    if perm.role_of(request.user) not in ("admin", "support"):
        return HttpResponseForbidden("Only Admins/Support can reserve slots.")
    lead = get_object_or_404(Lead, pk=pk)
    slot = get_object_or_404(ConsultationSlot, pk=slot_pk, status__in=["Open", "Reserved"])
    if request.method == "POST":
        Consultation.objects.get_or_create(slot=slot, lead=lead, defaults={"status": "Reserved"})
        if slot.status == "Open":
            slot.status = "Reserved"
            slot.save(update_fields=["status"])
        return redirect("lead_detail", pk=lead.pk)
    return redirect("lead_reserve_slot", pk=lead.pk)


@login_required
def resolve_followup_need(request, lead_id):
    lead = get_object_or_404(Lead, pk=lead_id)
    if not perm.can_edit(request.user, "followups"):
        return HttpResponseForbidden("You don't have permission to resolve follow-ups.")
    pending = Followup.objects.filter(lead=lead, followup_type="needs_attention", done=False)

    if request.method == "POST":
        pending_count = pending.count()
        form = FollowupForm(request.POST, initial={"lead": lead.pk, "followup_type": "needs_attention", "done": True})
        if form.is_valid():
            resolution = form.save(commit=False)
            resolution.lead = lead
            resolution.created_by = request.user
            resolution.done = True
            resolution.save()
            pending.exclude(pk=resolution.pk).update(done=True)
            # Clear the flag everywhere it surfaces for this lead: the cohort roster
            # (driven by open follow-ups) resolves automatically, and here we also
            # untick the daily-scoring flags that raised the attention.
            DailyScore.objects.filter(enrollment__lead=lead, needs_followup=True).update(needs_followup=False)
            messages.success(request, f"Resolved {pending_count} pending followup(s) for {lead.full_name}.")
            return redirect(request.POST.get("next") or reverse("record_list", args=["followups"]))
    else:
        form = FollowupForm(
            initial={
                "lead": lead.pk,
                "followup_type": "needs_attention",
                "due_date": timezone.localdate(),
                "done": True,
            }
        )

    return render(request, "leads/resolve_followup_need.html", {"lead": lead, "form": form, "pending": pending})
