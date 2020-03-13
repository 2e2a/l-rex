from django.contrib import messages
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.urls import reverse
from django.views import generic


class DefaultDeleteView(generic.DeleteView):
    title = 'Confirm deletion'
    success_message = 'Deletion successfull.'

    def get_success_message(self):
        return self.success_message

    def delete(self, *args, **kwargs):
        result = super().delete(*args, **kwargs)
        messages.success(self.request, self.get_success_message())
        return result

    @property
    def message(self):
        return 'Delete {} "{}"?'.format(self.object._meta.object_name, self.object)


class LeaveWarningMixin:

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if not context.get('disabled', False):
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
        data['disabled'] = self.is_disabled
        return data

    def _disable_form_inputs(self, element):
        if hasattr(element, 'field_classes'):
            element.field_classes += '  disabled'
            element.flat_attrs += '  disabled=True'
        if hasattr(element, 'inputs'):
            for helper_input in element.inputs:
                self._disable_form_inputs(helper_input)
        if hasattr(element, 'fields'):
            for helper_field in element.fields:
                self._disable_form_inputs(helper_field)
        if hasattr(element, 'layout') and hasattr(element.layout, 'fields'):
            for helper_field in element.layout.fields:
                self._disable_form_inputs(helper_field)

    def disable_form(self, form):
        for field in form.fields.values():
            field.widget.attrs['readonly'] = True
            field.widget.attrs['disabled'] = True
            if hasattr(form, 'helper'):
                self._disable_form_inputs(form.helper)

    def get_form(self, form_class=None):
        form = super().get_form(form_class=form_class)
        if self.is_disabled:
            self.disable_form(form)
            if  hasattr(self, 'helper'):
                self._disable_form_inputs(self.helper)
        return form

    def get(self, request, *args, **kwargs):
        if self.is_disabled:
            if hasattr(self, 'helper'):
                for helper_input in self.helper.inputs:
                    helper_input.field_classes += '  disabled'
                    helper_input.flat_attrs += '  disabled=True'
            if hasattr(self, 'formset'):
                for form in self.formset:
                    self.disable_form(form)
        return  super().get(request, *args, **kwargs)


class PaginationHelperMixin:

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'url_par': self.url_par(),
            'url_par_paginated': self.url_paginated(),
        })
        return context

    def url_par(self):
        url_par = ''
        for par, value in self.request.GET.items():
            if par != 'page':
                url_par += '&{}={}'.format(par, value)
        return url_par

    def url_paginated(self, url=None, page=None):
        if not url:
            url = ''
        if page is None:
            page = self.request.GET.get('page', None)
        url += '?page={}'.format(page if page else 1)
        return url + self.url_par()

    def reverse_paginated(self, to, **kwargs):
        if 'args' in kwargs:
            url = reverse(to, args=kwargs['args']) + self.url_par()
        else:
            url = reverse(to, kwargs=kwargs)
        return self.url_paginated(url, kwargs.get('page', None))

    def redirect_paginated(self, to, *args, **kwargs):
        url = self.reverse_paginated(to, **kwargs)
        return redirect(url)
