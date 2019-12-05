# Generated by Django 2.2.7 on 2019-12-05 11:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lrex_trial', '0002_remove_trial_rating_proof'),
    ]

    operations = [
        migrations.AlterField(
            model_name='questionnaireblock',
            name='randomization',
            field=models.CharField(blank=True, choices=[('pseudo', 'Pseudo-randomize'), ('true', 'Randomize'), ('none', 'Keep item order')], default='pseudo', help_text='Randomize items in each questionnaire block.', max_length=8),
        ),
    ]