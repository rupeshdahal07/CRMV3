from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "admin", "Admin"
        SUPPORT = "support", "Support"
        TEACHER = "teacher", "Teacher"
        TESTER = "tester", "Tester"
        STUDENT = "student", "Student"

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.SUPPORT)
    about = models.TextField(blank=True)
    contact_number = models.CharField(max_length=30, blank=True)
    plain_password = models.CharField(
        max_length=128,
        blank=True,
        help_text="Readable copy of the password — used for student accounts so staff can view/share login details.",
    )

    def __str__(self):
        return self.get_full_name() or self.username
