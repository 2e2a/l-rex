# Generated by Django 2.2.1 on 2019-06-03 09:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lrex_study', '0027_study_is_archived'),
    ]

    operations = [
        migrations.AddField(
            model_name='study',
            name='pseudo_randomize_question_order',
            field=models.BooleanField(default=False, help_text='Show questions in a random order, if multiple questions defined.'),
        ),
    ]