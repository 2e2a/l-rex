# Generated by Django 2.2.7 on 2020-02-19 16:48

from django.db import migrations, models
import markdownx.models


class Migration(migrations.Migration):

    dependencies = [
        ('lrex_study', '0004_auto_20200110_1139'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='study',
            name='link_block_instructions',
        ),
        migrations.RemoveField(
            model_name='study',
            name='link_instructions',
        ),
        migrations.AddField(
            model_name='study',
            name='block_instructions_label',
            field=models.CharField(default='Show/hide short instructions for this block', help_text='Label of the link to the short block instructions that the participant can access during  participation (if defined).', max_length=60),
        ),
        migrations.AddField(
            model_name='study',
            name='short_instructions',
            field=markdownx.models.MarkdownxField(blank=True, help_text='You can optionally provide a shorter version of the instructions that the participant can access at any point during participation as a reminder of the task.', max_length=3000, null=True),
        ),
        migrations.AlterField(
            model_name='study',
            name='instructions_label',
            field=models.CharField(default='Show/hide short instructions', help_text='Label of the link to the short instructions that the participant can access during participation (if defined).', max_length=60),
        ),
    ]