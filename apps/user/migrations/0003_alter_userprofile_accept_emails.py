# Generated by Django 3.2 on 2021-06-12 14:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lrex_user', '0002_auto_20210203_0613'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='accept_emails',
            field=models.BooleanField(default=False, help_text='Accept L-Rex notification e-mails about your studies and technical issues.'),
        ),
    ]
