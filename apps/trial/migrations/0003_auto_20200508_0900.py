# Generated by Django 2.2.11 on 2020-05-08 09:00

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('lrex_trial', '0002_auto_20200506_0814'),
    ]

    operations = [
        migrations.AlterField(
            model_name='trial',
            name='created',
            field=models.DateTimeField(blank=True, default=django.utils.timezone.now, null=True),
        ),
    ]
