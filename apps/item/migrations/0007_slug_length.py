# Generated by Django 2.1.7 on 2019-03-04 08:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lrex_item', '0006_item_question_order'),
    ]

    operations = [
        migrations.AlterField(
            model_name='item',
            name='slug',
            field=models.SlugField(max_length=230, unique=True),
        ),
    ]