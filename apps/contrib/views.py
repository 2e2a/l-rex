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
        response = super().get(request, *args, **kwargs)
        if self.is_disabled:
            if hasattr(self, 'formset'):
                for helper_input in self.formset.helper.inputs:
                    helper_input.field_classes += ' disabled'
                    helper_input.flat_attrs += ' disabled=True'
                for form in self.formset:
                    self.disable_form(form)
        return response


class FormsetView(generic.TemplateView):
    formset_factory = None
    custom_formset = None

    formset_class = None
    formset = None
    form_count = None

    def get_formset_queryset(self):
        raise NotImplementedError('Provide a queryset.')

    def get_form_count(self):
        return None

    def dispatch(self, request, *args, **kwargs):
        self.form_count = self.get_form_count()
        self.formset_class = self.formset_factory(
            form_count=self.form_count, custom_formset=self.custom_formset, study=self.study
        )
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        return {'study': self.study}

    def get(self, request, *args, **kwargs):
        self.formset = self.formset_class(queryset=self.get_formset_queryset(), form_kwargs=self.get_form_kwargs())
        if self.get_form_count() is None and self.get_formset_queryset().count() == 0:
            messages.info(
                self.request,
                'If you want to create multiple elements: save the first one, then a form for the next one will appear.'
            )
        return super().get(request, *args, **kwargs)

    def save_form(self, form, number):
        form.instance.save()

    def formset_valid(self):
        message = '{}s saved.'.format(self.formset_class.model._meta.verbose_name.capitalize())
        messages.success(self.request, message)

    def formset_invalid(self):
        pass

    def submit_redirect(self):
        raise NotImplementedError('Provide a submit redirect.')

    def post(self, request, *args, **kwargs):
        self.formset = self.formset_class(
            request.POST, request.FILES, queryset=self.get_formset_queryset(), form_kwargs=self.get_form_kwargs()
        )
        if self.formset.is_valid():
            instances = self.formset.save(commit=False)
            number = 0
            for form in self.formset:
                if form.instance.pk and form.cleaned_data.get('DELETE', False):
                    form.instance.delete()
                    continue
                if self.form_count or form.instance in instances or form.instance.pk:
                    self.save_form(form, number)
                number += 1
            self.formset_valid()
            if 'submit' in request.POST:
                return self.submit_redirect()
            return self.get(request, *args, **kwargs)
        else:
            self.formset_invalid()
        return super().get(request, *args, **kwargs)


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
