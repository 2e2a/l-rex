# Generated by Django 2.1.7 on 2019-03-07 07:29

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('lrex_experiment', '0007_ordering'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='experiment',
            options={'ordering': ['study', 'title']},
        ),
    ]