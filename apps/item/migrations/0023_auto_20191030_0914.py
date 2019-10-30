# Generated by Django 2.2.5 on 2019-10-30 09:14

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('lrex_materials', '0002_copy_experiments'),
        ('lrex_item', '0022_auto_20190930_0850'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='itemlist',
            options={'ordering': ['materials', 'number']},
        ),
        migrations.AddField(
            model_name='item',
            name='materials',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='lrex_materials.Materials'),
        ),
        migrations.AddField(
            model_name='itemlist',
            name='materials',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='lrex_materials.Materials'),
        ),
    ]