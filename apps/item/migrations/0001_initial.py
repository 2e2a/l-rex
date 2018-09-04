# Generated by Django 2.1 on 2018-09-04 12:59

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('lrex_experiment', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Item',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('number', models.IntegerField(help_text='Number of the item')),
                ('condition', models.CharField(help_text='Condition of the item (character limit: 8)', max_length=8)),
            ],
            options={
                'ordering': ['number', 'condition'],
            },
        ),
        migrations.CreateModel(
            name='ItemList',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('number', models.IntegerField()),
                ('experiment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='lrex_experiment.Experiment')),
            ],
            options={
                'ordering': ['number'],
            },
        ),
        migrations.CreateModel(
            name='AudioLinkItem',
            fields=[
                ('item_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='lrex_item.Item')),
                ('url', models.URLField(help_text='Link to the audio file (e.g., https://yourserver.org/item1a.ogg).', verbose_name='URL')),
            ],
            bases=('lrex_item.item',),
        ),
        migrations.CreateModel(
            name='TextItem',
            fields=[
                ('item_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='lrex_item.Item')),
                ('text', models.TextField(help_text='Content of the item (character limit: 1024).', max_length=1024)),
            ],
            bases=('lrex_item.item',),
        ),
        migrations.AddField(
            model_name='itemlist',
            name='items',
            field=models.ManyToManyField(to='lrex_item.Item'),
        ),
        migrations.AddField(
            model_name='item',
            name='experiment',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='lrex_experiment.Experiment'),
        ),
    ]
