# Generated by Django 2.2.5 on 2019-10-23 13:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lrex_trial', '0030_auto_20191009_0820'),
    ]

    operations = [
        migrations.AlterField(
            model_name='trial',
            name='subject_id',
            field=models.CharField(blank=True, help_text='Provide an identification number/name (as instructed by the experimenter).', max_length=200, null=True, verbose_name='ID'),
        ),
    ]