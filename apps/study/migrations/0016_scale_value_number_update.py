# Generated by Django 2.1.1 on 2018-09-24 07:35
from datetime import timedelta

from django.db import migrations
from django.utils.timezone import now


def update(apps, schema_editor):
    Question = apps.get_model('lrex_study', 'Question')
    for question  in Question.objects.all():
        scale_values = question.scalevalue_set.all().order_by('pk')
        for i, scale_value in enumerate(scale_values):
            scale_value.number = i
            scale_value.save(update_fields=['number'])


class Migration(migrations.Migration):

    dependencies = [
        ('lrex_study', '0015_question_number_update'),
    ]

    operations = [
        migrations.RunPython(update, reverse_code=migrations.RunPython.noop),
    ]