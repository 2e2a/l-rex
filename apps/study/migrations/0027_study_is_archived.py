# Generated by Django 2.2 on 2019-04-25 07:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lrex_study', '0026_study_use_blocks_update'),
    ]

    operations = [
        migrations.AddField(
            model_name='study',
            name='is_archived',
            field=models.BooleanField(default=False),
        ),
    ]
