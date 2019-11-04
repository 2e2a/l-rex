from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse
from django.views import generic

from . import models
from . import forms


class UserProfileCreateView(LoginRequiredMixin, SuccessMessageMixin, generic.CreateView):
    model = models.UserProfile
    title = 'User settings'
    template_name = 'lrex_contrib/crispy_form.html'
    form_class = forms.ProfileForm
    success_message = 'User settings successfully updated.'

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('home')


class UserProfileUpdateView(LoginRequiredMixin, SuccessMessageMixin, generic.UpdateView):
    model = models.UserProfile
    title = 'User settings'
    template_name = 'lrex_contrib/crispy_form.html'
    form_class = forms.ProfileForm
    success_message = 'User settings successfully updated.'

    def get_object(self, queryset=None):
        return self.request.user.userprofile

    def get_success_url(self):
        return reverse('home')
