from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse
from django.views import generic

from apps.contrib import views as contrib_views

from . import models
from . import forms


User = get_user_model()


class UserAccountCreateView(LoginRequiredMixin, SuccessMessageMixin, generic.CreateView):
    model = models.UserProfile
    title = 'User settings'
    template_name = 'lrex_home/base_form.html'
    form_class = forms.AccountForm
    success_message = 'User settings successfully updated.'

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('home')


class UserAccountUpdateView(LoginRequiredMixin, SuccessMessageMixin, generic.UpdateView):
    model = models.UserProfile
    title = 'Account settings'
    template_name = 'lrex_user/account.html'
    form_class = forms.AccountForm
    success_message = 'User settings successfully updated.'

    def get_object(self, queryset=None):
        return self.request.user.userprofile

    def get_success_url(self):
        return reverse('home')


class UserAccountDeleteView(LoginRequiredMixin, contrib_views.DefaultDeleteView):
    model = User
    template_name = 'lrex_home/base_confirm_delete.html'
    message = 'Delete user account? Note that all studies and collected data will be deleted.'

    def get_object(self, queryset=None):
        return self.request.user

    def get_success_url(self):
        return reverse('home')


