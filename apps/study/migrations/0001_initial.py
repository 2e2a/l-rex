# Generated by Django 2.1 on 2018-09-11 08:20

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


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
                ('question', models.CharField(help_text='Question text for this item (e.g. "How acceptable is this sentence?")', max_length=1000)),
                ('legend', models.CharField(blank=True, help_text='Legend to clarify the scale (e.g. "1 = bad, 5 = good")', max_length=1000, null=True)),
            ],
            options={
                'ordering': ['pk'],
            },
        ),
        migrations.CreateModel(
            name='ScaleValue',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('label', models.CharField(help_text='Provide a label for this point of the scale.', max_length=50)),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='lrex_study.Question')),
            ],
            options={
                'ordering': ['pk'],
            },
        ),
        migrations.CreateModel(
            name='Study',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(help_text='Give your study a name.', max_length=200, unique=True)),
                ('slug', models.SlugField(unique=True)),
                ('item_type', models.CharField(choices=[('txt', 'Text'), ('aul', 'Audio Link')], default='txt', help_text='The items can be plain text or links to audio files (self-hosted).', max_length=3)),
                ('rating_instructions', models.TextField(help_text='These instructions will be presented to the participant before the experiment begins.', max_length=1024)),
                ('password', models.CharField(help_text='This password will be required to participate in the study.', max_length=200)),
                ('require_participant_id', models.BooleanField(default=False, help_text='Enable if you want participants to enter some ID before participation.')),
                ('end_date', models.DateField(blank=True, help_text='If you want to set a participation deadline, enter a date in the format YYYY-MM-DD.', null=True)),
                ('trial_limit', models.IntegerField(blank=True, help_text='If you want to set a maximal number of participants, enter a number.', null=True, verbose_name='Maximal number of participants')),
                ('is_published', models.BooleanField(default=False, help_text='Enable to publish your study. It will then be available for participation.')),
                ('progress', models.CharField(choices=[('00-std-crt', 'Create a study'), ('10-qst-crt', 'Create a question'), ('20-exp-crt', 'Create an experiment'), ('29-exp-cmp', 'Complete the experiment creation'), ('30-std-qnr-gen', 'Generate questionnaires'), ('40-std-pub', 'Publish the study')], default='00-std-crt', max_length=16)),
                ('creator', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='question',
            name='study',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='lrex_study.Study'),
        ),
    ]
