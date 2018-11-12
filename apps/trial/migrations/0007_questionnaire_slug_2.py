from django.db import migrations


def gen_slug(apps, schema_editor):
    Questionnaire = apps.get_model('lrex_trial', 'Questionnaire')
    for questionnaire in Questionnaire.objects.all():
        questionnaire.slug = '{}-{}'.format(questionnaire.study.slug, questionnaire.number)
        questionnaire.save(update_fields=['slug'])


class Migration(migrations.Migration):

    dependencies = [
        ('lrex_trial', '0006_questionnaire_slug_1'),
    ]

    operations = [
        migrations.RunPython(gen_slug, reverse_code=migrations.RunPython.noop),
    ]
