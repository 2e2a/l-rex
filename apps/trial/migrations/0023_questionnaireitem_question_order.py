# Generated by Django 2.2.1 on 2019-06-03 09:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lrex_trial', '0022_questionnaire_randomization_optional'),
    ]

    operations = [
        migrations.AddField(
            model_name='questionnaireitem',
            name='question_order',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
    ]
