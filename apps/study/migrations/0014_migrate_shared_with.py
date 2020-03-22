from django.contrib.auth import get_user_model
from django.db import migrations


def migrate(apps, schema_editor):
    Study = apps.get_model('lrex_study', 'Study')
    User = apps.get_model('auth', 'User')
    for study in Study.objects.exclude(shared_with_old=None):
        user_names = [user_name for user_name in study.shared_with_old.split(',')]
        users = User.objects.filter(username__in=user_names)
        study.shared_with.set(users)
        study.save()


class Migration(migrations.Migration):

    dependencies = [
        ('lrex_study', '0013_study_shared_with'),
    ]

    operations = [
        migrations.RunPython(migrate),
    ]