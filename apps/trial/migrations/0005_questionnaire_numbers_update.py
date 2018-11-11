from django.db import migrations


def update_number(apps, schema_editor):
    Study = apps.get_model('lrex_study', 'Study')
    for study in Study.objects.all():
        for i, questionnaire in enumerate(study.questionnaire_set.all()):
            questionnaire.number = i + 1
            questionnaire.save(update_fields=['number'])


class Migration(migrations.Migration):

    dependencies = [
        ('lrex_trial', '0004_questionnaire_number'),
    ]

    operations = [
        migrations.RunPython(update_number, reverse_code=migrations.RunPython.noop),
    ]
