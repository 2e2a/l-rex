# Generated by Django 2.2.14 on 2020-12-05 09:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lrex_study', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='scalevalue',
            name='label',
            field=models.CharField(help_text='Provide a label for this point of the scale.', max_length=1000),
        ),
    ]