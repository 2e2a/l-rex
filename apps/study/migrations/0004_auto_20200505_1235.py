# Generated by Django 2.2.11 on 2020-05-05 12:35

from django.db import migrations, models
import markdownx.models


class Migration(migrations.Migration):

    dependencies = [
        ('lrex_study', '0003_auto_20200505_1234'),
    ]

    operations = [
        migrations.AlterField(
            model_name='study',
            name='consent_form_label',
            field=models.CharField(default='Consent form', help_text='Label for "Consent form" used during participation.', max_length=40),
        ),
        migrations.AlterField(
            model_name='study',
            name='consent_form_text',
            field=markdownx.models.MarkdownxField(blank=True, help_text='This text informs participants about the procedure andpurpose of the study. It will be shown to the participants before thestudy begins. It should include a privacy statement: whether anypersonal data is collected and how it will be processed and stored.', max_length=5000, null=True),
        ),
    ]
