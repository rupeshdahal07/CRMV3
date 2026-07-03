from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import User


class EmailOrUsernameAuthenticationForm(AuthenticationForm):
    username = forms.CharField(label="Username or Email", widget=forms.TextInput(attrs={"autofocus": True}))


class UserCreateForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ["username", "first_name", "last_name", "email", "role"]


class UserEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "role", "is_active"]


class TeacherProfileForm(forms.ModelForm):
    new_password = forms.CharField(
        label="New Password",
        required=False,
        widget=forms.PasswordInput(render_value=False),
        help_text="Leave blank to keep your current password.",
    )

    class Meta:
        model = User
        fields = ["first_name", "last_name", "username", "email", "contact_number", "about"]
        widgets = {"about": forms.Textarea(attrs={"rows": 3})}

    def clean_username(self):
        username = self.cleaned_data["username"]
        qs = User.objects.filter(username=username).exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("That username is already taken.")
        return username
