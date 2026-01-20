from django_registration.forms import RegistrationForm
from django import forms
from django.contrib.auth import get_user_model
from apps.contrib import forms as contrib_forms

from . import models


User = get_user_model()


class AccountForm(contrib_forms.CrispyModelForm):

    class Meta:
        model = models.UserProfile
        fields = [
            'accept_emails',
        ]


class EmailChangeForm(contrib_forms.CrispyModelForm):
    confirm_password = forms.CharField(
        label='Confirm password',
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'password', 'autofocus': True}),
    )
    optional_label_ignore_fields = [
        'email',
    ]

    def clean_confirm_password(self):
        password = self.cleaned_data['confirm_password']
        if not self.user.check_password(password):
            raise forms.ValidationError('Invalid password.')
        return password

    class Meta:
        model = User
        fields = [
            'email',
            'confirm_password',
        ]

    def __init__(self, **kwargs):
        self.user = kwargs.pop('user')
        super().__init__(**kwargs)
        self.fields['email'].required = True


class UserRegistrationForm(RegistrationForm):
    captcha = forms.CharField(
        required=True,
        label='What\'s 5 plus 4?',
        help_text='Solve this to prove you are human (captcha).'
    )

    class Meta(RegistrationForm.Meta):
        fields = [
            User.USERNAME_FIELD,
            User.get_email_field_name(),
            "password1",
            "password2",
            "captcha",
        ]

    def clean_captcha(self):
        captcha = self.cleaned_data['captcha']
        captcha = captcha.strip()
        if captcha != '9':
            raise forms.ValidationError('Captcha failed.')
        return captcha
