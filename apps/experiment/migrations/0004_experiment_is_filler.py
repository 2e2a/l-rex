# Generated by Django 2.1.1 on 2018-10-11 09:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lrex_experiment', '0003_update_slugs'),
    ]

    operations = [
        migrations.AddField(
            model_name='experiment',
            name='is_filler',
            field=models.BooleanField(default=False),
        ),
    ]
