# Generated by Django 2.2.5 on 2019-09-17 08:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lrex_experiment', '0013_experiment_block'),
    ]

    operations = [
        migrations.AddField(
            model_name='experiment',
            name='item_list_distribution',
            field=models.CharField(choices=[('latin-square', 'Latin-Square Distribution'), ('all-to-all', 'Show all conditions to all participants')], default='latin-square', help_text='How to distribute items across lists.', max_length=16),
        ),
    ]
