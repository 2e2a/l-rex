# Generated by Django 2.1.7 on 2019-03-04 09:15

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('lrex_experiment', '0006_slug_length'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='experiment',
            options={'ordering': ['slug']},
        ),
    ]