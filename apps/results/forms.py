from django import forms

from . import models

class UserBinaryResponseForm(forms.ModelForm):

     class Meta:
         model = models.UserBinaryResponse
         fields = ['yes']
