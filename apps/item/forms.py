from django import forms


class PregenerateItemsForm(forms.Form):
    num_items = forms.IntegerField()
    num_conditions = forms.IntegerField()

