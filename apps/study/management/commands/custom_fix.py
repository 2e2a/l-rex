from django.core.management.base import BaseCommand

from apps.study import models as study_models


class Command(BaseCommand):
    help = 'Placeholder for one time server fixes.'

    def handle(self, *args, **options):
        pass
