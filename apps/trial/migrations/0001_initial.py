# Generated by Django 2.2.11 on 2020-03-25 12:41

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import markdownx.models
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('lrex_study', '0001_initial'),
        ('lrex_item', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Questionnaire',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('slug', models.SlugField(max_length=110, unique=True)),
                ('number', models.IntegerField()),
                ('item_lists', models.ManyToManyField(to='lrex_item.ItemList')),
                ('study', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='questionnaires', to='lrex_study.Study')),
            ],
            options={
                'ordering': ['number'],
            },
        ),
        migrations.CreateModel(
            name='QuestionnaireItem',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('number', models.IntegerField()),
                ('question_order', models.CharField(blank=True, max_length=200, null=True)),
                ('item', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='lrex_item.Item')),
                ('questionnaire', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='questionnaire_items', to='lrex_trial.Questionnaire')),
            ],
            options={
                'ordering': ['number'],
            },
        ),
        migrations.CreateModel(
            name='Trial',
            fields=[
                ('slug', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('created', models.DateTimeField(default=django.utils.timezone.now)),
                ('ended', models.DateTimeField(blank=True, null=True)),
                ('subject_id', models.CharField(blank=True, help_text='Provide an identification number/name (as instructed by the experimenter).', max_length=200, null=True, verbose_name='ID')),
                ('is_test', models.BooleanField(default=False)),
                ('questionnaire', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='lrex_trial.Questionnaire')),
            ],
            options={
                'ordering': ['created'],
            },
        ),
        migrations.CreateModel(
            name='Rating',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('question', models.IntegerField(default=0)),
                ('comment', models.CharField(blank=True, max_length=2000, null=True)),
                ('questionnaire_item', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ratings', to='lrex_trial.QuestionnaireItem')),
                ('scale_value', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='lrex_study.ScaleValue')),
                ('trial', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='lrex_trial.Trial')),
            ],
            options={
                'ordering': ['trial', 'questionnaire_item', 'question'],
            },
        ),
        migrations.CreateModel(
            name='QuestionProperty',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('number', models.IntegerField()),
                ('scale_order', models.CharField(blank=True, max_length=200, null=True)),
                ('questionnaire_item', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='question_properties', to='lrex_trial.QuestionnaireItem')),
            ],
            options={
                'ordering': ['number'],
            },
        ),
        migrations.CreateModel(
            name='QuestionnaireBlock',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('block', models.IntegerField()),
                ('instructions', markdownx.models.MarkdownxField(blank=True, help_text='These instructions will be presented to the participant before the questionnaire block begins.', max_length=5000, null=True)),
                ('short_instructions', markdownx.models.MarkdownxField(blank=True, help_text='You can optionally provide a shorter version of the block instructions that the participant can access again during participation as a reminder of the task.', max_length=3000, null=True)),
                ('randomization', models.CharField(blank=True, choices=[('pseudo', 'Pseudo-randomize'), ('true', 'Randomize'), ('none', 'Keep item order')], default='pseudo', help_text='Randomize items in each questionnaire block.', max_length=8)),
                ('study', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='questionnaire_blocks', to='lrex_study.Study')),
            ],
            options={
                'ordering': ['block'],
            },
        ),
        migrations.CreateModel(
            name='DemographicValue',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('value', models.CharField(max_length=2000)),
                ('field', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='lrex_study.DemographicField')),
                ('trial', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='demographics', to='lrex_trial.Trial')),
            ],
            options={
                'ordering': ['trial', 'field'],
            },
        ),
    ]
