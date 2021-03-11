# Generated by Django 2.2.14 on 2021-02-12 08:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lrex_study', '0004_study_use_vertical_scale_layout'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='demographicfield',
            options={'ordering': ['study', 'number']},
        ),
        migrations.AddField(
            model_name='demographicfield',
            name='number',
            field=models.IntegerField(default=0),
        ),
    ]
