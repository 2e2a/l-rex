from django.conf import settings


def announcements(request):
    return {
        'announcements': settings.LREX_ANNOUNCEMENTS,
    }