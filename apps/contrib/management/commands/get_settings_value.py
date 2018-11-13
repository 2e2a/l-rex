from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Extract a settings value'

    def add_arguments(self, parser):
        parser.add_argument('setting', type=str)
        parser.add_argument('path', type=str, nargs='?')

    def handle(self, *args, **options):
        setting = options['setting']
        path = options['path'].split(',') if options['path'] else []
        result = getattr(settings, setting)
        for next in path:
            result = result[next]
        print(result)
