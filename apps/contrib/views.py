from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse
from django.views import generic


class DefaultDeleteView(generic.DeleteView):
    title = 'Confirm Delete'
    template_name = 'lrex_contrib/confirm_delete.html'
    success_message = 'Deletion successfull.'

    def get_success_message(self):
        return self.success_message

    def delete(self, *args, **kwargs):
        result = super().delete(*args, **kwargs)
        messages.success(self.request, self.get_success_message())
        return result

    @property
    def message(self):
        return 'Delete "{}"?'.format(self.object)


class LeaveWarningMixin:

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'leave_warning': True,
        })
        return context


class DisableFormMixin:

    @property
    def is_disabled(self):
        raise NotImplementedError

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['is_disabled'] = self.is_disabled
        return data

    def _disbable_form(self, form):
        for field in form.fields.values():
            field.widget.attrs['readonly'] = True
            field.widget.attrs['disabled'] = True

    def get_form(self, form_class=None):
        form = super().get_form(form_class=form_class)
        if self.is_disabled:
            self._disbable_form(form)
            for helper_input in form.helper.inputs:
                helper_input.field_classes += '  disabled'
                helper_input.flat_attrs += '  disabled=True'
        return form

    def get(self, request, *args, **kwargs):
        if self.is_disabled:
            if hasattr(self, 'helper'):
                for helper_input in self.helper.inputs:
                    helper_input.field_classes += '  disabled'
                    helper_input.flat_attrs += '  disabled=True'
            if hasattr(self, 'formset'):
                for form in self.formset:
                    self._disbable_form(form)
        return  super().get(request, *args, **kwargs)


class PaginationHelperMixin:

    def url_paginated(self, url):
        page = self.request.GET.get('page', None)
        if page:
            url += '?page={}'.format(page)
        return url

    def reverse_paginated(self, to, **kwargs):
        if 'args' in kwargs:
            url = reverse(to, args=kwargs['args'])
        else:
            url = reverse(to, kwargs=kwargs)
        return self.url_paginated(url)

    def redirect_paginated(self, to, *args, **kwargs):
        url = self.reverse_paginated(to, **kwargs)
        return redirect(url)
