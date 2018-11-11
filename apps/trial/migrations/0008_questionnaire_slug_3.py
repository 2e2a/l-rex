import uuid

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('lrex_trial', '0007_questionnaire_slug_2'),
    ]

    operations = [
        migrations.AlterField(
            model_name='questionnaire',
            name='slug',
            field=models.SlugField(unique=True),
        ),
    ]
