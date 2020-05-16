# Generated by Django 2.2.11 on 2020-05-16 09:32

from django.db import migrations
import markdownx.models


class Migration(migrations.Migration):

    dependencies = [
        ('lrex_study', '0004_auto_20200505_1235'),
    ]

    operations = [
        migrations.AlterField(
            model_name='study',
            name='consent_form_text',
            field=markdownx.models.MarkdownxField(blank=True, help_text='This text informs participants about the procedure and purpose of the study. It will be shown to the participants before the study begins. It should include a privacy statement: whether any personal data is collected and how it will be processed and stored.', max_length=5000, null=True),
        ),
    ]
