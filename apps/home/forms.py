from html import unescape
from datetime import timedelta
from django import forms
from django.conf import settings
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.utils.timezone import now

from apps.contrib import forms as contrib_forms
from apps.study.models import Study


class InvoiceRequestForm(contrib_forms.CrispyForm):
    email = forms.EmailField()
    name = forms.CharField()
    address = forms.CharField(widget=forms.Textarea(attrs={'rows': 5}))
    study = forms.ModelChoiceField(
        queryset=Study.objects.none(), required=False, label='Study', help_text='Recent studies.',
    )
    comment = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 4}), label='Comment')
    AMOUNT_CHOICES = [
        ('10', '10€'),
        ('25', '25€'),
        ('50', '50€'),
        ('100', '100€'),
        ('', 'Other amount'),
    ]
    amount = forms.CharField(widget=forms.Select(
        choices=AMOUNT_CHOICES), initial='25', required=False, label='Choose an amount',
        help_text='Including 19% taxes.'
    )
    other_amount = forms.IntegerField(required=False, label='Other amount in Euro', help_text='Including 19% taxes.')

    optional_label_ignore_fields = ('amount', 'other_amount')

    email_subject = 'L-Rex invoice request confirmation'
    email_template = 'emails/invoice_request.txt'
    tax_rate = 19

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        study = kwargs.pop('study')
        super().__init__(*args, **kwargs)
        if user.is_authenticated:
            self.fields['email'].initial = user.email
            year_ago = now().date() - timedelta(days=365)
            self.fields['study'].queryset = Study.objects.filter(
                creator=user, has_invoice=False, created_date__gte=year_ago
            )
            self.fields['study'].initial = study
        else:
            self.fields['study'].widget = forms.HiddenInput()

    def clean(self):
        data = super().clean()
        if not data['amount'] and not data['other_amount']:
            raise forms.ValidationError('Please set an amount.')
        amount = data['other_amount'] if data['other_amount'] else int(data['amount'])
        amount_taxes = amount * self.tax_rate / (100 + self.tax_rate)
        data.update({
            'amount_pre_tax': amount - amount_taxes,
            'amount_taxes': amount_taxes,
            'amount_total': amount,
        })
        return data

    def send_mail(self):
        from_email = settings.DEFAULT_FROM_EMAIL
        recipients = [self.cleaned_data['email']]
        message = unescape(render_to_string(self.email_template, self.cleaned_data))
        email = EmailMessage(self.email_subject, message, from_email, recipients, bcc=[from_email])
        email.send()
