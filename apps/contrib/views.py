from django.contrib import messages
from django.shortcuts import redirect
from django.template.loader import render_to_string
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
            self._disable_form_inputs(form.helper)

    def get_form(self, form_class=None):
        form = super().get_form(form_class=form_class)
        if self.is_disabled:
            self.disable_form(form)
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


class ActionsMixin:
    actions = None
    secondary_actions = None
    disable_actions = ([], [])

    ACTION_CSS_BUTTON_PRIMARY = 'btn btn-sm mx-1 btn-primary'
    ACTION_CSS_BUTTON_SECONDARY = 'btn btn-sm mx-1 btn-secondary'
    ACTION_CSS_BUTTON_WARNING = 'btn btn-sm mx-1 btn-warning'

    def _get_action_html(self, action_type, action, disabled):
        action_context = {
            'type': action_type,
            'disabled': disabled,
        }
        if action_type == 'link':
            name, url, ccs = action
            action_context.update({
                'name': name,
                'url': url,
                'css': ccs,
            })
        elif action_type == 'button':
            name, value, ccs = action
            action_context.update({
                'name': name,
                'value': value,
                'css': ccs,
            })
        elif action_type == 'dropdown':
            id, name, urls, ccs = action
            action_context.update({
                'name': name,
                'id': id,
                'urls': urls,
                'css': ccs,
            })
        elif action_type == 'form':
            form, helper = action
            if disabled and hasattr(self, 'disable_form'):
                self.disable_form(form)
            action_context.update({
                'form': form,
                'helper': helper,
            })
        return render_to_string('lrex_contrib/action.html', action_context)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.actions:
            actions_html = []
            for i, action in enumerate(self.actions):
                disabled = self.disable_actions and i in self.disable_actions[0]
                actions_html.append(self._get_action_html(action[0], action[1:], disabled))
            context.update({
                'actions': actions_html,
            })
        if self.secondary_actions:
            actions_html = []
            for i, action in enumerate(self.secondary_actions):
                disabled = self.disable_actions and i in self.disable_actions[0]
                action += ('dropdown-item',)
                actions_html.append(self._get_action_html(action[0], action[1:], disabled))
            context.update({
                'secondary_actions': actions_html,
            })

        return context
