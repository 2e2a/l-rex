# Generated by Django 2.2.14 on 2020-12-10 08:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lrex_item', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='itemquestion',
            name='scale_labels',
            field=models.TextField(blank=True, help_text='Individual rating scale labels for this item, separated by commas (e.g. "1,2,3,4,5"). If a label contains a comma itself, escape it with "\\" (e.g. "A,B,Can\'t decide\\, I like both"). Note that this will only overwrite the displayed labels, but the responses will be saved according to the general scale specified in the study settings.', max_length=10000, null=True),
        ),
    ]
