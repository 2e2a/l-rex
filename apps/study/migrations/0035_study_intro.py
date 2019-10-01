# Generated by Django 2.2.5 on 2019-09-30 12:48

from django.db import migrations
import markdownx.models


class Migration(migrations.Migration):

    dependencies = [
        ('lrex_study', '0034_auto_20190930_0921'),
    ]

    operations = [
        migrations.AddField(
            model_name='study',
            name='intro',
            field=markdownx.models.MarkdownxField(blank=True, help_text='Welcome text presented to the participant at first.', max_length=5000, null=True),
        ),
    ]