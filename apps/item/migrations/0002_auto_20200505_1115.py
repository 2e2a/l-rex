# Generated by Django 2.2.11 on 2020-05-05 11:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lrex_item', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='item',
            name='condition',
            field=models.CharField(help_text='Condition of the item (character limit: 16).', max_length=16),
        ),
    ]
