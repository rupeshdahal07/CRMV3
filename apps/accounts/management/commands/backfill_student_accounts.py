from django.core.management.base import BaseCommand

from apps.accounts.services import create_student_account
from apps.leads.models import Lead


class Command(BaseCommand):
    help = "Creates a student login account for every existing Lead that doesn't already have one."

    def handle(self, *args, **options):
        leads = Lead.objects.filter(student_account__isnull=True)
        count = leads.count()
        for lead in leads:
            account = create_student_account(lead)
            self.stdout.write(f"  {lead.full_name} -> {account.username}")
        self.stdout.write(self.style.SUCCESS(f"Created {count} student account(s)."))
