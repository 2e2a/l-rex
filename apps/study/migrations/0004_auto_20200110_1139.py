# Generated by Django 2.2.7 on 2020-01-10 11:39

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('lrex_study', '0003_study_is_finished'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='study',
            options={'ordering': ['-created_date', 'title']},
        ),
    ]
