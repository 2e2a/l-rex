# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-03-26 08:42
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('lrex_item', '0001_initial'),
        ('contenttypes', '0002_remove_content_type_name'),
        ('lrex_setup', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Trial',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('number', models.IntegerField()),
                ('setup', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='lrex_setup.Setup')),
            ],
            options={
                'ordering': ['number'],
            },
        ),
        migrations.CreateModel(
            name='TrialList',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('list', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='lrex_item.List')),
                ('trial', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='lrex_trial.Trial')),
            ],
        ),
        migrations.CreateModel(
            name='UserTrial',
            fields=[
                ('slug', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('creation_date', models.DateTimeField(default=django.utils.timezone.now)),
                ('participant', models.EmailField(blank=True, max_length=254)),
                ('trial', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='lrex_trial.Trial')),
            ],
            options={
                'ordering': ['-creation_date'],
            },
        ),
        migrations.CreateModel(
            name='UserTrialItem',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('number', models.IntegerField()),
                ('object_id', models.PositiveIntegerField()),
                ('content_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contenttypes.ContentType')),
                ('usertrial', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='lrex_trial.UserTrial')),
            ],
        ),
    ]
