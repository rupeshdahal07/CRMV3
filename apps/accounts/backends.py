from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q

User = get_user_model()


class EmailOrUsernameBackend(ModelBackend):
    """Allows login with either username or email (case-insensitive)."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        identifier = username or kwargs.get(User.USERNAME_FIELD)
        if identifier is None or password is None:
            return None
        try:
            user = User.objects.get(Q(username__iexact=identifier) | Q(email__iexact=identifier))
        except User.DoesNotExist:
            # Run the hasher anyway to mitigate timing-based user enumeration.
            User().set_password(password)
            return None
        except User.MultipleObjectsReturned:
            user = User.objects.filter(Q(username__iexact=identifier) | Q(email__iexact=identifier)).order_by("id").first()
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
