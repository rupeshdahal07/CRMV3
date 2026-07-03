"""User & role management (Admin) plus the staff self-service profile."""

from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import SetPasswordForm
from django.db.models import Q
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render

from apps.core import permissions as perm
from apps.core.decorators import admin_required

from .forms import TeacherProfileForm, UserCreateForm, UserEditForm
from .models import User


@login_required
def my_profile(request):
    if perm.role_of(request.user) not in ("admin", "support", "teacher"):
        return HttpResponseForbidden("This page isn't available for your role.")
    if request.method == "POST":
        form = TeacherProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            new_password = form.cleaned_data.get("new_password")
            user = form.save(commit=False)
            if new_password:
                user.set_password(new_password)
            user.save()
            if new_password:
                update_session_auth_hash(request, user)
            messages.success(request, "Profile updated.")
            return redirect("my_profile")
    else:
        form = TeacherProfileForm(instance=request.user)
    return render(request, "accounts/my_profile.html", {"form": form})


@admin_required
def user_list(request):
    users = User.objects.all().order_by("username")

    q = request.GET.get("q", "").strip()
    if q:
        users = users.filter(
            Q(username__icontains=q)
            | Q(first_name__icontains=q)
            | Q(last_name__icontains=q)
            | Q(email__icontains=q)
        )

    role = request.GET.get("role", "").strip()
    valid_roles = {value for value, _ in User.Role.choices}
    if role in valid_roles:
        users = users.filter(role=role)

    return render(
        request,
        "accounts/user_list.html",
        {
            "users": users,
            "q": q,
            "role": role,
            "role_choices": User.Role.choices,
        },
    )


@admin_required
def user_create(request):
    if request.method == "POST":
        form = UserCreateForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_staff = user.role == "admin"
            user.save()
            messages.success(request, f"User {user.username} created.")
            return redirect("user_list")
    else:
        form = UserCreateForm()
    return render(request, "accounts/user_form.html", {"form": form, "is_new": True})


@admin_required
def user_edit(request, pk):
    obj = get_object_or_404(User, pk=pk)
    if request.method == "POST":
        form = UserEditForm(request.POST, instance=obj)
        if form.is_valid():
            if obj.pk == request.user.pk and not form.cleaned_data["is_active"]:
                messages.error(request, "You can't deactivate your own account.")
            else:
                user = form.save(commit=False)
                user.is_staff = user.role == "admin"
                user.save()
                messages.success(request, f"User {user.username} updated.")
                return redirect("user_list")
    else:
        form = UserEditForm(instance=obj)
    return render(request, "accounts/user_form.html", {"form": form, "is_new": False, "obj": obj})


@admin_required
def user_reset_password(request, pk):
    obj = get_object_or_404(User, pk=pk)
    if request.method == "POST":
        form = SetPasswordForm(obj, request.POST)
        if form.is_valid():
            form.save()
            if obj.pk == request.user.pk:
                update_session_auth_hash(request, obj)
            messages.success(request, f"Password reset for {obj.username}.")
            return redirect("user_list")
    else:
        form = SetPasswordForm(obj)
    return render(request, "accounts/user_reset_password.html", {"form": form, "obj": obj})


@admin_required
def user_delete(request, pk):
    obj = get_object_or_404(User, pk=pk)
    if obj.pk == request.user.pk:
        messages.error(request, "You can't delete your own account.")
        return redirect("user_list")
    if request.method == "POST":
        obj.delete()
        messages.success(request, f"User {obj.username} deleted.")
        return redirect("user_list")
    return render(request, "accounts/user_confirm_delete.html", {"obj": obj})
