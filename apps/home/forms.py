from django import forms
from django.conf import settings
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from apps.contrib import forms as contrib_forms


class InvoiceRequestForm(contrib_forms.CrispyForm):
    email = forms.EmailField()
    subject = forms.CharField(initial='Nutzung des L-Rex Dienstes', label='Invoice subject')
    AMOUNT_CHOICES = [
        ('', '---'),
        ('10', '10€'),
        ('25', '25€'),
        ('50', '50€'),
        ('100', '100€'),
    ]
    amount = forms.CharField(widget=forms.Select(choices=AMOUNT_CHOICES), required=False, label='Choose an amount')
    other_amount = forms.IntegerField(required=False, label='Other amount in Euro')
    including_taxes = forms.BooleanField(required=False, label='Including 19% taxes')

    optional_label_ignore_fields = ('amount', 'other_amount')

    email_subject = 'L-Rex invoice request confirmation'
    email_template = 'emails/invoice_request.txt'

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        super().__init__(*args, **kwargs)
        if user.is_authenticated:
            self.fields['email'].initial = user.email

    def clean(self):
        data = super().clean()
        if not data['amount'] and not data['other_amount']:
            raise forms.ValidationError('Please set an amount.')
        amount = data['other_amount'] if data['other_amount'] else int(data['amount'])
        if data['including_taxes']:
            data.update({
                'amount_pre_tax': amount * .81,
                'amount_taxes': amount * .19,
                'amount_total': amount,
            })
        else:
            amount_taxes = amount * .19
            data.update({
                'amount_pre_tax': amount,
                'amount_taxes': amount_taxes,
                'amount_total': amount + amount_taxes,
            })
        return data

    def send_mail(self):
        from_email = settings.DEFAULT_FROM_EMAIL
        recipients = [self.cleaned_data['email']]
        message = render_to_string(self.email_template, self.cleaned_data)
        email = EmailMessage(self.email_subject, message, from_email, recipients, bcc=[from_email])
        email.send()
