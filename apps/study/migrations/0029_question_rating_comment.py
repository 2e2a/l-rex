# Generated by Django 2.2.2 on 2019-07-16 10:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lrex_study', '0028_study_pseudo_randomize_question_order'),
    ]

    operations = [
        migrations.AddField(
            model_name='question',
            name='rating_comment',
            field=models.CharField(choices=[('none', 'None'), ('optional', 'Optional'), ('required', 'Required')], default='none', help_text='Let the participant add a comment to the rating (free text).', max_length=10),
        ),
    ]