# Generated by Django 2.2.7 on 2019-12-07 07:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lrex_study', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='study',
            name='answer_question_message',
            field=models.CharField(default='Please answer this question.', help_text='Error message shown to participant if the question was not answered.', max_length=500),
        ),
        migrations.AlterField(
            model_name='study',
            name='answer_questions_message',
            field=models.CharField(default='Please answer all questions.', help_text='Error message shown to participant if a question was not answered.', max_length=500),
        ),
        migrations.AlterField(
            model_name='study',
            name='feedback_message',
            field=models.CharField(default='Please note the following feedback.', help_text='Message indicating that feedback is shown for some ratings.', max_length=500),
        ),
    ]
