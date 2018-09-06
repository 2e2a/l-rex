# Generated by Django 2.1 on 2018-09-06 11:44

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('lrex_item', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ItemQuestion',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('question', models.CharField(help_text='TODO This text will precede the stimulus (e.g. "How acceptable is this sentence?")', max_length=200)),
                ('scale_labels', models.CharField(blank=True, help_text='TODO comma separated', max_length=500, null=True)),
                ('legend', models.TextField(blank=True, help_text='TODO This legend will appear below the stimulus to clarify the scale (e.g. "1 = bad, 5 = good").', max_length=1024, null=True)),
                ('item', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='lrex_item.Item')),
            ],
            options={
                'ordering': ['question'],
            },
        ),
    ]
