# Generated by Django 2.2.14 on 2020-12-10 04:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lrex_study', '0002_auto_20201205_0932'),
    ]

    operations = [
        migrations.AlterField(
            model_name='scalevalue',
            name='label',
            field=models.TextField(help_text='Provide a label for this point of the scale.', max_length=1000),
        ),
    ]
