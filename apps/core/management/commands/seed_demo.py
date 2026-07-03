import datetime

from django.core.management.base import BaseCommand

from apps.accounts.models import User
from apps.cohorts.models import Cohort, Curriculum, CurriculumChapter, DailyScore, Enrollment, Followup
from apps.consultations.models import Consultation, ConsultationSlot, PostConsultationCall
from apps.leads.models import Lead

DEMO_PASSWORD = "nobigo123"


class Command(BaseCommand):
    help = "Seed sample data drawn from the real Nobigo sheets, for demo/testing."

    def handle(self, *args, **options):
        admin, _ = User.objects.get_or_create(
            username="admin", defaults={"role": "admin", "is_staff": True, "is_superuser": True}
        )
        if admin.role != "admin":
            admin.role = "admin"
            admin.save()

        sanjit, _ = User.objects.get_or_create(
            username="sanjit", defaults={"first_name": "Sanjit", "last_name": "Bhandari", "role": "teacher"}
        )
        sujata, _ = User.objects.get_or_create(
            username="sujata", defaults={"first_name": "Sujata", "last_name": "Sharma", "role": "support"}
        )

        # Give demo staff a known password so the app is immediately loginable.
        for u in (admin, sanjit, sujata):
            u.set_password(DEMO_PASSWORD)
            u.plain_password = DEMO_PASSWORD
            u.save()

        lead1, _ = Lead.objects.update_or_create(
            user_code="4286",
            defaults=dict(
                full_name="Asim Shrestha",
                phone="98XXXXXXXX",
                signup_date=datetime.date(2026, 6, 30),
                why_learn_japanese="study",
                journey_progress="joined_satisfied",
                level="N5",
                hiragana_katakana="Hiragana only",
                skill_focus="Vocab",
                survey_language="JP",
                already_in_consultancy=True,
                pain_fee=True,
                pain_documentation=True,
                topic_consultancy=True,
                topic_language_school=True,
                call_status="Completed",
                preferred_call_language="Nepali",
                agent=sujata,
                notes="Already in a consultancy; worried about fee transparency and document checklist.",
            ),
        )

        lead2, _ = Lead.objects.update_or_create(
            user_code="4279",
            defaults=dict(
                full_name="Dinesh Khadka",
                phone="9816300484",
                signup_date=datetime.date(2026, 6, 30),
                journey_progress="self_study_starting",
                level="Absolute beginner",
                visa_category="SSW",
                call_status="No Answer",
                notes="call not received",
            ),
        )

        slot, _ = ConsultationSlot.objects.update_or_create(
            date=datetime.date(2026, 7, 2),
            counselor=sujata,
            defaults=dict(time=datetime.time(17, 0), status="Completed", meeting_link="https://zoom.us/j/000000"),
        )
        Consultation.objects.update_or_create(
            slot=slot,
            lead=lead1,
            defaults=dict(status="Completed", pmf_score=4, user_seriousness="High", class_interest=True),
        )

        PostConsultationCall.objects.update_or_create(
            lead=lead1,
            defaults=dict(
                call_date=datetime.date(2026, 7, 6),
                called_by=sujata,
                call_status="Completed",
                cohort_interest=True,
                notes="Wants fee transparency and language school comparison covered before enrolling.",
            ),
        )

        curriculum, _ = Curriculum.objects.get_or_create(name="N5 Foundations", defaults={"level": "N5"})
        for day in range(1, 15):
            CurriculumChapter.objects.get_or_create(
                curriculum=curriculum,
                day_number=day,
                defaults=dict(week_number=1 if day <= 7 else 2, title=f"Chapter {day}", assigned_teacher=sanjit),
            )

        cohort, _ = Cohort.objects.get_or_create(
            code="C1",
            defaults=dict(
                level="N5",
                start_date=datetime.date(2026, 6, 30),
                class_time=datetime.time(19, 0),
                assigned_teacher=sanjit,
                curriculum=curriculum,
                status="Started",
            ),
        )

        enrollment, _ = Enrollment.objects.get_or_create(
            lead=lead1, cohort=cohort, defaults={"enrolled_date": datetime.date(2026, 6, 30)}
        )

        for day in range(1, 15):
            DailyScore.objects.get_or_create(
                enrollment=enrollment,
                day_number=day,
                defaults=dict(
                    date=datetime.date(2026, 6, 30),
                    status="Present",
                    class_presence=5 if day == 1 else None,
                    scored_by=sanjit,
                ),
            )

        Followup.objects.get_or_create(
            lead=lead2,
            due_date=datetime.date(2026, 7, 2),
            defaults=dict(followup_type="general", remark="busy in the office call after 6 PM", created_by=sujata),
        )

        self.stdout.write(
            self.style.SUCCESS(
                "Seed data created: 2 leads, 1 consultation, 1 cohort with curriculum, "
                "1 enrollment with 14 days scored."
            )
        )
        self.stdout.write(f"  Staff logins (password '{DEMO_PASSWORD}'): admin / sujata / sanjit")
