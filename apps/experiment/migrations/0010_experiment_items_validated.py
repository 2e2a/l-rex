# Generated by Django 2.1.7 on 2019-04-12 08:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lrex_experiment', '0009_remove_experiment_progress'),
    ]

    operations = [
        migrations.AddField(
            model_name='experiment',
            name='items_validated',
            field=models.BooleanField(default=False),
        ),
    ]
