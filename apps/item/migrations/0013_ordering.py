# Generated by Django 2.1.7 on 2019-03-19 07:38

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('lrex_item', '0012_ordering'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='item',
            options={'ordering': ['number', 'condition']},
        ),
    ]