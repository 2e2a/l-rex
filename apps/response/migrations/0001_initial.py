# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-03-18 10:24
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('lrex_experiment', '0002_auto_20170318_1024'),
    ]

    operations = [
        migrations.CreateModel(
            name='BinaryResponse',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('question', models.CharField(max_length=200)),
                ('legend', models.TextField(max_length=1024)),
                ('yes', models.CharField(max_length=200)),
                ('no', models.CharField(max_length=200)),
                ('experiment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='lrex_experiment.Experiment')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]