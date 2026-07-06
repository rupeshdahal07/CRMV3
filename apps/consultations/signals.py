"""
Keep a consultation slot's status in sync with its attendee count.

Rule: a slot with 0 attendees is "Open"; with 1+ it's "Reserved". This is applied
whenever an attendee (Consultation) is added or removed, through any code path.
Terminal statuses set by staff ("Completed" / "Cancelled") are never overridden.
"""

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import Consultation, ConsultationSlot

# Only these statuses are auto-managed; others are deliberate staff decisions.
AUTO_STATES = {"Open", "Reserved"}


def sync_slot_status(slot):
    if slot is None or slot.status not in AUTO_STATES:
        return
    desired = "Reserved" if slot.attendees.exists() else "Open"
    if slot.status != desired:
        slot.status = desired
        slot.save(update_fields=["status"])


@receiver(post_save, sender=Consultation)
def _attendee_saved(sender, instance, **kwargs):
    sync_slot_status(instance.slot)


@receiver(post_delete, sender=Consultation)
def _attendee_deleted(sender, instance, **kwargs):
    # The slot may itself have been deleted (cascade); look it up safely.
    slot = ConsultationSlot.objects.filter(pk=instance.slot_id).first()
    sync_slot_status(slot)
