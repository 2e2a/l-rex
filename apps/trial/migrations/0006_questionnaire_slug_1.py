from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lrex_trial', '0005_questionnaire_numbers_update'),
    ]

    operations = [
        migrations.AddField(
            model_name='questionnaire',
            name='slug',
            field=models.SlugField(null=True),
        ),
    ]
