from django.db import migrations


def run(apps, schema_editor):
    Experiments = apps.get_model('lrex_experiment', 'Experiment')
    Materials = apps.get_model('lrex_materials', 'Materials')
    Materials.objects.all().delete()
    fields = [field.name for field in Experiments._meta.get_fields()]
    fields.remove('id')
    for experiment in Experiments.objects.all():
        field_dict = {}
        for field in fields:
            if hasattr(experiment, field):
                field_dict.update({ field: getattr(experiment, field)})
        Materials.objects.create(**field_dict)


class Migration(migrations.Migration):

    dependencies = [
        ('lrex_materials', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(run, reverse_code=migrations.RunPython.noop),
    ]
