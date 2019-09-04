# Generated by Django 2.2.4 on 2019-08-22 10:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lrex_item', '0016_audiolinkitem_description'),
    ]

    operations = [
        migrations.AddField(
            model_name='audiolinkitem',
            name='urls',
            field=models.CharField(help_text='Links to the audio files separated by commas (e.g., https://yourserver.org/item1a-i.ogg,https://yourserver.org/item1a-ii.ogg). ', max_length=5000, null=True, verbose_name='URLs'),
        ),
    ]