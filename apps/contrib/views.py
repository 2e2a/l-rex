from django.views import generic


class DefaultDeleteView(generic.DeleteView):
    title = 'Confirm Delete'
    template_name = 'lrex_contrib/confirm_delete.html'

    @property
    def message(self):
        return 'Delete "{}"?'.format(self.object)
