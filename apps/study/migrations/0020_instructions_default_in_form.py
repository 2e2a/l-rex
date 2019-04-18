# Generated by Django 2.1.7 on 2019-04-08 07:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lrex_study', '0019_remove_study_progress'),
    ]

    operations = [
        migrations.AlterField(
            model_name='study',
            name='instructions',
            field=models.TextField(blank=True, help_text='These instructions will be presented to the participant before the experiment begins.', max_length=5000, null=True),
        ),
    ]