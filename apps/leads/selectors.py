"""Read-side helpers for a Lead: the merged activity timeline and notes feed."""


def build_lead_notes(lead):
    """Every free-text note / concern / feedback tied to this lead, from anywhere
    in the funnel, each tagged with where it came from. Newest dated first."""
    items = []

    def add(source, text, date=None, kind="note", author=None):
        text = (text or "").strip()
        if text:
            items.append({"source": source, "text": text, "date": date, "kind": kind, "author": author})

    # --- Lead record itself ---
    add("Lead · Call notes", lead.notes, lead.call_date or (lead.created_at.date() if lead.created_at else None),
        "note", lead.agent)
    add("Lead · Other concern", lead.pain_other, kind="concern")
    add("Lead · Other topic", lead.topic_other, kind="concern")
    if lead.curiosity_note:
        level = lead.get_curiosity_level_display() or "—"
        add(f"Lead · Curiosity ({level})", lead.curiosity_note, kind="note")

    concern_flags = [
        (lead.pain_fee, "Fee concern"),
        (lead.pain_visa_rejection, "Visa rejected"),
        (lead.pain_documentation, "Document submitted"),
        (lead.documentation_concern, "Documentation concern"),
        (lead.pain_accommodation, "Accommodation concern"),
        (lead.topic_consultancy, "Consultancy doubts"),
        (lead.topic_language_school, "Language school concerns"),
        (lead.topic_jobs, "Job concern"),
    ]
    flagged = [label for on, label in concern_flags if on]
    if flagged:
        add("Lead · Flagged concerns", ", ".join(flagged), kind="concern")

    # --- Consultations ---
    for c in lead.consultations.select_related("slot", "slot__counselor").all():
        tag = f"Consultation · {c.slot.date or 'no date'}"
        add(f"{tag} · Main concern", c.main_concern, c.slot.date, "concern", c.slot.counselor)
        add(f"{tag} · Note", c.note, c.slot.date, "note", c.slot.counselor)

    # --- Post-consultation calls ---
    for pc in lead.post_consultation_calls.select_related("called_by").all():
        tag = f"Post-consult call · {pc.call_date or 'no date'}"
        add(f"{tag} · Feedback", pc.consultation_feedback, pc.call_date, "feedback", pc.called_by)
        add(f"{tag} · Notes", pc.notes, pc.call_date, "note", pc.called_by)

    # --- Enrollments + daily scores ---
    for e in lead.enrollments.select_related("cohort").all():
        add(f"Enrollment · {e.cohort} · Remarks", e.remarks, e.enrolled_date, "note")
        add(f"Enrollment · {e.cohort} · Follow-up outcome", e.followup_outcome, e.enrolled_date, "feedback")
        for s in e.daily_scores.exclude(note="").select_related("scored_by").all():
            add(f"Daily score · {e.cohort} · Day {s.day_number}", s.note, s.date, "note", s.scored_by)

    # --- Follow-ups ---
    for f in lead.followups.select_related("created_by").all():
        done = " (done)" if f.done else ""
        add(f"Follow-up · {f.get_followup_type_display()}{done}", f.remark, f.due_date, "followup", f.created_by)

    dated = sorted((i for i in items if i["date"]), key=lambda x: x["date"], reverse=True)
    undated = [i for i in items if not i["date"]]
    return dated + undated


def build_followup_history(lead):
    """Every follow-up for this lead — pending and resolved — with its source and
    current status. Also surfaces admissions 'Follow-up Needed' call flags."""
    items = []

    for f in lead.followups.select_related("enrollment__cohort", "created_by").all():
        if f.followup_type == "needs_attention":
            source = f"Class scoring · {f.enrollment.cohort}" if f.enrollment_id else "Attention flag"
        else:
            source = f.get_followup_type_display()
        items.append({
            "pk": f.pk,  # editable record
            "type": f.get_followup_type_display(),
            "source": source,
            "detail": f.remark,
            "date": f.due_date,
            "author": f.created_by,
            "done": f.done,
            "is_attention": f.followup_type == "needs_attention",
        })

    # Current admissions call flags (state, not a resolvable follow-up record).
    if lead.call_status == "Follow-up Needed":
        items.append({
            "pk": None, "type": "Lead call", "source": "Lead call status",
            "detail": (lead.notes or "")[:140], "date": lead.call_date,
            "author": lead.agent, "done": False, "is_attention": True,
        })
    for pc in lead.post_consultation_calls.filter(call_status="Follow-up Needed").select_related("called_by"):
        items.append({
            "pk": None, "type": "Post-consult call", "source": "Post-consult call status",
            "detail": (pc.notes or "")[:140], "date": pc.call_date,
            "author": pc.called_by, "done": False, "is_attention": True,
        })

    # Pending first, then newest date first.
    items.sort(key=lambda x: (x["done"], -(x["date"].toordinal() if x["date"] else 0)))
    return items



def build_lead_timeline(lead):
    """A chronological, cross-stage activity feed for the lead detail page."""
    events = []
    events.append(
        {
            "date": lead.signup_date or lead.created_at.date(),
            "type": "signup",
            "label": "Signed up",
            "detail": f"Level: {lead.get_level_display()}" if lead.level else "",
        }
    )
    if lead.call_status:
        events.append(
            {
                "date": lead.call_date or lead.created_at.date(),
                "type": "call",
                "label": f"Call outcome — {lead.call_status}",
                "detail": (f"Agent: {lead.agent}. " if lead.agent else "") + (lead.notes[:150] if lead.notes else ""),
            }
        )
    for c in lead.consultations.select_related("slot", "slot__counselor").all():
        events.append(
            {
                "date": c.slot.date,
                "type": "consultation",
                "label": f"Consultation — {c.status}",
                "detail": (f"Counselor: {c.slot.counselor}. " if c.slot.counselor else "")
                + (f"PMF: {c.pmf_score}/5" if c.pmf_score else ""),
            }
        )
    for pc in lead.post_consultation_calls.select_related("called_by", "preferred_cohort").all():
        events.append(
            {
                "date": pc.call_date,
                "type": "post_call",
                "label": f"Post-consultation call — {pc.call_status or 'logged'}",
                "detail": (f"Cohort interest: {'Yes' if pc.cohort_interest else 'No'}. ")
                + (f"Preferred: {pc.preferred_cohort}. " if pc.preferred_cohort else "")
                + (f"By: {pc.called_by}" if pc.called_by else ""),
            }
        )
    for e in lead.enrollments.select_related("cohort").all():
        events.append(
            {
                "date": e.enrolled_date,
                "type": "enrollment",
                "label": f"Enrolled in {e.cohort}",
                "detail": f"Level {e.cohort.level or '—'} · Teacher: {e.cohort.assigned_teacher or '—'}",
            }
        )
        scores = list(e.daily_scores.exclude(status="").order_by("day_number"))
        if scores:
            present = sum(1 for s in scores if s.status == "Present")
            last = scores[-1]
            events.append(
                {
                    "date": last.date or e.enrolled_date,
                    "type": "attendance",
                    "label": f"Attendance in {e.cohort}: {present}/{len(scores)} days present",
                    "detail": f"Latest: Day {last.day_number} — {last.status or '—'} · Nobigo Score so far: {e.total_score}",
                }
            )
    for f in lead.followups.all():
        events.append(
            {
                "date": f.due_date,
                "type": "followup",
                "label": f"Follow-up ({f.get_followup_type_display()}){' — done' if f.done else ''}",
                "detail": f.remark[:150] if f.remark else "",
            }
        )
    events = [ev for ev in events if ev["date"]]
    events.sort(key=lambda ev: ev["date"])
    return events
