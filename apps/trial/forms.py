from django import forms

from .models import Trial


class TrialForm(forms.ModelForm):
    password = forms.CharField(max_length=200, widget=forms.PasswordInput)

    class Meta:
        model = Trial
        fields = ['id']

    def __init__(self, *args, **kwargs):
        self.study = kwargs.pop('study')
        super().__init__(*args, **kwargs)
        self.fields['id'].required = not self.study.allow_anonymous

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data['password'] != self.study.password:
            raise forms.ValidationError('Invalid password.')
        return cleaned_data
