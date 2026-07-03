"""Consultation slot detail + reserving a lead into a slot."""

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render

from apps.core import permissions as perm
from apps.leads.models import Lead

from .models import Consultation, ConsultationSlot


@login_required
def consultation_slot_detail(request, pk):
    slot = get_object_or_404(ConsultationSlot, pk=pk)
    if perm.role_of(request.user) == "teacher" and slot.counselor_id != request.user.id:
        return HttpResponseForbidden("You can only view your own consultation slots.")
    can_edit_slot = perm.can_edit(request.user, "consultation-slots") and (
        perm.role_of(request.user) != "teacher" or slot.counselor_id == request.user.id
    )
    return render(
        request,
        "consultations/slot_detail.html",
        {
            "slot": slot,
            "attendees": slot.attendees.select_related("lead").all(),
            "can_edit_slot": can_edit_slot,
        },
    )


@login_required
def consultation_slot_add_attendee(request, pk):
    slot = get_object_or_404(ConsultationSlot, pk=pk)
    if perm.role_of(request.user) not in ("admin", "support"):
        return HttpResponseForbidden("Only Admins/Support can reserve leads into a slot.")
    already_reserved_lead_ids = slot.attendees.values_list("lead_id", flat=True)
    available_leads = Lead.objects.exclude(id__in=already_reserved_lead_ids).order_by("full_name")
    if request.method == "POST":
        lead_id = request.POST.get("lead_id")
        if lead_id:
            Consultation.objects.get_or_create(slot=slot, lead_id=lead_id, defaults={"status": "Reserved"})
            if slot.status == "Open":
                slot.status = "Reserved"
                slot.save(update_fields=["status"])
        return redirect("consultation_slot_detail", pk=slot.pk)
    return render(request, "consultations/slot_add_attendee.html", {"slot": slot, "available_leads": available_leads})
