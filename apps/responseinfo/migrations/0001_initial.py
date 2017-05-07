# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-04-29 06:19
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('lrex_setup', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ResponseInfo',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('question', models.CharField(max_length=200)),
                ('legend', models.TextField(max_length=1024)),
                ('instructions', models.TextField(max_length=1024)),
                ('reponse_type', models.CharField(choices=[('bin', 'Binary')], default='bin', max_length=3)),
            ],
        ),
        migrations.CreateModel(
            name='BinaryResponseInfo',
            fields=[
                ('responseinfo_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='lrex_responseinfo.ResponseInfo')),
                ('yes', models.CharField(max_length=200)),
                ('no', models.CharField(max_length=200)),
            ],
            bases=('lrex_responseinfo.responseinfo',),
        ),
        migrations.AddField(
            model_name='responseinfo',
            name='setup',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='lrex_setup.Setup'),
        ),
    ]