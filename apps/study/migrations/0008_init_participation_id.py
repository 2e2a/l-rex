from django.db import migrations


def migrate(apps, schema_editor):
    Study = apps.get_model('lrex_study', 'Study')
    for study in Study.objects.filter(require_participant_id=True):
        study.participant_id = 'enter'
        study.save()


class Migration(migrations.Migration):

    dependencies = [
        ('lrex_study', '0007_auto_20200309_1531'),
    ]

    operations = [
        migrations.RunPython(migrate),
    ]