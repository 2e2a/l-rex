# Generated by Django 3.2 on 2021-04-22 04:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lrex_item', '0002_auto_20201210_0817'),
    ]

    operations = [
        migrations.AlterField(
            model_name='itemfeedback',
            name='scale_values',
            field=models.TextField(help_text='Scale values, separated by commas (e.g. "1,3"). If a label contains a comma itself, escape it with "\\" (e.g. "A,B,Can\'t decide\\, I like both"). The feedback will be shown to the participant if one of these ratings is selected.', max_length=10000),
        ),
    ]
