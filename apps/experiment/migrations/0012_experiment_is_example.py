# Generated by Django 2.2.2 on 2019-07-03 12:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lrex_experiment', '0011_items_validated_update'),
    ]

    operations = [
        migrations.AddField(
            model_name='experiment',
            name='is_example',
            field=models.BooleanField(default=False, help_text='Items of this experiment will automatically be in the item block 0.'),
        ),
    ]
