from apps.contrib import forms as crispy_forms

from . import models


class ProfileForm(crispy_forms.CrispyModelForm):

    class Meta:
        model = models.UserProfile
        fields = [
            'accept_emails',
        ]
