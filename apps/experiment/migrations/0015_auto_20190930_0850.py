# Generated by Django 2.2.5 on 2019-09-30 08:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lrex_experiment', '0014_experiment_item_list_distribution'),
    ]

    operations = [
        migrations.AlterField(
            model_name='experiment',
            name='block',
            field=models.IntegerField(default=-1, help_text='Items will all be in this block (-1 = no automatic block assignment).'),
        ),
        migrations.AlterField(
            model_name='experiment',
            name='is_example',
            field=models.BooleanField(default=False, help_text='Items will all be in block 0 (preceding all other materials).'),
        ),
    ]
