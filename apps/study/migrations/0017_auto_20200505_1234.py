# Generated by Django 2.2.11 on 2020-05-05 12:34

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('lrex_study', '0016_auto_20200429_0825'),
    ]

    operations = [
        migrations.RenameField(
            model_name='study',
            old_name='privacy_statement_label',
            new_name='consent_form_label',
        ),
        migrations.RenameField(
            model_name='study',
            old_name='privacy_statement',
            new_name='consent_form_text',
        ),
    ]