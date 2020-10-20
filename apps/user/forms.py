from apps.contrib import forms as contrib_forms

from . import models


class AccountForm(contrib_forms.CrispyModelForm):

    class Meta:
        model = models.UserProfile
        fields = [
            'accept_emails',
        ]
