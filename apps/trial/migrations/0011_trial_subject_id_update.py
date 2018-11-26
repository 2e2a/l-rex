from django.db import migrations


def update_id(apps, schema_editor):
    Trial = apps.get_model('lrex_trial', 'Trial')
    for trial in Trial.objects.all():
        trial.subject_id = trial.id
        trial.save(update_fields=['subject_id'])


class Migration(migrations.Migration):

    dependencies = [
        ('lrex_trial', '0010_trial_subject_id'),
    ]

    operations = [
        migrations.RunPython(update_id, reverse_code=migrations.RunPython.noop),
    ]
