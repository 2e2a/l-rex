from django.db import migrations


def run(apps, schema_editor):
    Materials = apps.get_model('lrex_materials', 'Materials')
    Item = apps.get_model('lrex_item', 'Item')
    for item in Item.objects.all():
        item.materials = Materials.objects.get(slug=item.experiment.slug)
        item.save(update_fields=['materials'])
    ItemList = apps.get_model('lrex_item', 'ItemList')
    for item_list in ItemList.objects.all():
        item_list.materials = Materials.objects.get(slug=item_list.experiment.slug)
        item_list.save(update_fields=['materials'])


class Migration(migrations.Migration):

    dependencies = [
        ('lrex_item', '0023_auto_20191030_0914'),
    ]

    operations = [
        migrations.RunPython(run, reverse_code=migrations.RunPython.noop),
    ]
