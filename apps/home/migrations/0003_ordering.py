# Generated by Django 2.2 on 2019-04-18 09:01

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('lrex_home', '0002_slug_length'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='news',
            options={'ordering': ['-date']},
        ),
    ]
