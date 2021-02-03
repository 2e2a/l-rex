from django.conf import settings
from django.db import models


class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    accept_emails = models.BooleanField(
        default=False,
        help_text='Allow L-Rex admin to contact me via e-mail about important technical issues, e.g., server problems.',
    )
