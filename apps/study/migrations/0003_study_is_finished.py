# Generated by Django 2.2.7 on 2020-01-10 09:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lrex_study', '0002_auto_20191207_0759'),
    ]

    operations = [
        migrations.AddField(
            model_name='study',
            name='is_finished',
            field=models.BooleanField(default=False, help_text='Enable to finish study participation.'),
        ),
    ]