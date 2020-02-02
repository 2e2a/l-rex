# Generated by Django 2.2.7 on 2020-02-02 12:28

from django.db import migrations
import markdownx.models


class Migration(migrations.Migration):

    dependencies = [
        ('lrex_study', '0005_study_short_instructions'),
    ]

    operations = [
        migrations.AlterField(
            model_name='study',
            name='short_instructions',
            field=markdownx.models.MarkdownxField(blank=True, help_text='You can optionally provide a shorter version of the instruction that the participant can access at any point during participation as a reminder of the task.', max_length=3000, null=True),
        ),
    ]
