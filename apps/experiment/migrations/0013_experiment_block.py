# Generated by Django 2.2.2 on 2019-07-03 12:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lrex_experiment', '0012_experiment_is_example'),
    ]

    operations = [
        migrations.AddField(
            model_name='experiment',
            name='block',
            field=models.IntegerField(default=-1, help_text='Items of this experiment will automatically be in this item block (-1 disabled).'),
        ),
    ]