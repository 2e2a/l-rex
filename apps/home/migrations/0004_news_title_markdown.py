# Generated by Django 2.2.1 on 2019-06-07 13:12

from django.db import migrations
import markdownx.models


class Migration(migrations.Migration):

    dependencies = [
        ('lrex_home', '0003_ordering'),
    ]

    operations = [
        migrations.AlterField(
            model_name='news',
            name='text',
            field=markdownx.models.MarkdownxField(max_length=5000),
        ),
    ]