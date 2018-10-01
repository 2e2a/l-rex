from allauth.account.forms import SignupForm


class FixedAutofocusSignupForm(SignupForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        del self.fields['username'].widget.attrs['autofocus']
        self.fields['email'].widget.attrs.update({'autofocus': 'autofocus'})



