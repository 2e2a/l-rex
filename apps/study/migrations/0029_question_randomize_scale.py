# Generated by Django 2.2.2 on 2019-07-10 11:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lrex_study', '0028_study_pseudo_randomize_question_order'),
    ]

    operations = [
        migrations.AddField(
            model_name='question',
            name='randomize_scale',
            field=models.BooleanField(default=False, help_text='Show scales in a pseudo-random order.'),
        ),
    ]