# Generated by Django 2.2.5 on 2019-11-06 12:47

import apps.contrib.datefield
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import markdownx.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Question',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('number', models.IntegerField(default=0)),
                ('question', models.CharField(help_text='Question text for this item (e.g. "How acceptable is this sentence?").', max_length=1000)),
                ('legend', models.CharField(blank=True, help_text='Legend to clarify the scale (e.g. "1 = bad, 5 = good").', max_length=1000, null=True)),
                ('randomize_scale', models.BooleanField(default=False, help_text='Show scale labels in random order.')),
                ('rating_comment', models.CharField(choices=[('none', 'None'), ('optional', 'Optional'), ('required', 'Required')], default='none', help_text='Let the participant add a comment to the rating (free text).', max_length=10)),
            ],
            options={
                'ordering': ['study', 'number'],
            },
        ),
        migrations.CreateModel(
            name='Study',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(help_text='Give your study a name.', max_length=100)),
                ('slug', models.SlugField(max_length=110, unique=True)),
                ('item_type', models.CharField(choices=[('txt', 'Plain text'), ('mkd', 'Rich text with markdown'), ('aul', 'Audio links')], default='txt', help_text='The items can be plain text or markdown rich text or links to audio files (self-hosted).', max_length=3)),
                ('use_blocks', models.BooleanField(default=False, help_text='Enable if you want to divide the questionnaire into separate parts (blocks) with individual instructions.')),
                ('pseudo_randomize_question_order', models.BooleanField(default=False, help_text='Show questions in random order (if multiple questions are defined).')),
                ('enable_item_rating_feedback', models.BooleanField(default=False, help_text='Allows you to define feedback shown to participants for individual item ratings.')),
                ('password', models.CharField(blank=True, help_text='This password will be required to participate in the study.', max_length=200, null=True)),
                ('instructions', markdownx.models.MarkdownxField(blank=True, help_text='These instructions will be presented to the participant before the experiment begins.', max_length=5000, null=True)),
                ('require_participant_id', models.BooleanField(default=False, help_text='Enable if you want participants to enter an ID before participation.', verbose_name='Participant ID required')),
                ('end_date', apps.contrib.datefield.DateField(blank=True, help_text='Set a participation deadline.', null=True)),
                ('trial_limit', models.IntegerField(blank=True, help_text='If you want to set a maximal number of participants, enter a number.', null=True, verbose_name='Maximal number of participants')),
                ('contact_name', models.CharField(blank=True, help_text='This name will be shown to participants as part of the contact information before the study begins.', max_length=1000, null=True)),
                ('contact_email', models.EmailField(blank=True, help_text='This e-mail address will be shown to participants as part of the contact information before the study begins.', max_length=254, null=True)),
                ('contact_affiliation', models.CharField(blank=True, help_text='This affiliation (e.g., university or research institute) will be shown to participants as part of the contact information before the study begins.', max_length=1000, null=True)),
                ('contact_details', markdownx.models.MarkdownxField(blank=True, help_text='You can optionally provide additional information about you and/or the research project (e.g., "This study is part of the research project XY, for more information, see ..."). This information will be shown to participants before the study begins.', max_length=5000, null=True)),
                ('privacy_statement', markdownx.models.MarkdownxField(blank=True, help_text='This statement will be shown to the participants before the study begins. It should state whether the study is fully anonymous or not. If you ask for individual IDs or personal data in your study, the privacy statement should include the following information: for what purpose is the ID/personal data collected, how long will the data be stored in non-anonymized form, and who is responsible for data processing?', max_length=5000, null=True)),
                ('intro', markdownx.models.MarkdownxField(blank=True, help_text='This text will be presented to the participants on the first page.', max_length=5000, null=True)),
                ('outro', markdownx.models.MarkdownxField(blank=True, help_text='This text will be presented to the participants on the last page.', max_length=5000, null=True)),
                ('continue_label', models.CharField(default='Continue', help_text='Label of the "Continue" button used during participation.', max_length=40)),
                ('privacy_statement_label', models.CharField(default='Privacy statement', help_text='Label for "Privacy statement" used during participation.', max_length=40)),
                ('contact_label', models.CharField(default='Contact', help_text='Label for "Contact" used during participation.', max_length=40)),
                ('instructions_label', models.CharField(default='Instructions', help_text='Label of the "Instructions" link used during participation.', max_length=40)),
                ('optional_label', models.CharField(default='optional', help_text='Label used for user input fields that can be optional, e.g. comment.', max_length=40)),
                ('comment_label', models.CharField(default='Comment', help_text='Label used for the comment field.', max_length=40)),
                ('answer_question_message', models.CharField(default='Please answer this question.', help_text='Error message shown to participant, if the question was not answered.', max_length=500)),
                ('answer_questions_message', models.CharField(default='Please answer all questions.', help_text='Error message shown to participant, if a question was not answered.', max_length=500)),
                ('feedback_message', models.CharField(default='Please note the following feedback.', help_text='Message indicating that feedback is shown for some ratings (only if feedback feature is enabled).', max_length=500)),
                ('is_published', models.BooleanField(default=False, help_text='Enable to publish your study. It will then be available for participation.')),
                ('shared_with', models.CharField(blank=True, help_text='Give other users access to the study. Enter comma-separated user names (e.g. "user1, user2").', max_length=200, null=True)),
                ('created_date', apps.contrib.datefield.DateField(default=django.utils.timezone.now, editable=False)),
                ('is_archived', models.BooleanField(default=False)),
                ('creator', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_date'],
            },
        ),
        migrations.CreateModel(
            name='ScaleValue',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('number', models.IntegerField(default=0)),
                ('label', models.CharField(help_text='Provide a label for this point of the scale.', max_length=50)),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='lrex_study.Question')),
            ],
            options={
                'ordering': ['question', 'number'],
            },
        ),
        migrations.AddField(
            model_name='question',
            name='study',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='lrex_study.Study'),
        ),
        migrations.CreateModel(
            name='DemographicField',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='You can enter a demographic question (e.g., "age" or "native languages"). The participants will have to answer it (free text input) at the beginning of the study.', max_length=500, verbose_name='question')),
                ('study', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='lrex_study.Study')),
            ],
            options={
                'ordering': ['study', 'pk'],
            },
        ),
    ]
