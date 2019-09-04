from django.contrib import messages
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

