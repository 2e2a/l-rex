from django.urls import reverse
from django.db import models

class Item(models.Model):
    number = models.IntegerField()
    condition = models.CharField(max_length=8)
    experiment = models.ForeignKey(
        'lrex_experiment.Experiment',
        on_delete=models.CASCADE
    )

    class Meta:
        ordering = ['number', 'condition']

    def __str__(self):
        return '{}{}'.format(self.number, self.condition)


class TextItem(Item):
    text = models.TextField(max_length=1024)

    def get_absolute_url(self):
        return reverse('textitem-update', args=[self.experiment.setup.slug, self.experiment.slug, self.pk])


class List(models.Model):
    number = models.IntegerField()
    experiment = models.ForeignKey(
        'lrex_experiment.Experiment',
        on_delete=models.CASCADE
    )

    class Meta:
        ordering = ['number']

    @property
    def items(self):
        list_items = ListItem.objects.filter(list=self)
        items = [list_item.item.textitem for list_item in list_items]
        return items

    def __str__(self):
        return '{}-list-{}'.format(self.experiment, self.number)

    def next(self, last_list):
        next_list =  List.objects.filter(experiment=last_list.experiment, number__gt=last_list.number).first()
        if not next_list:
            next_list =  List.objects.first()
        return next_list


class ListItem(models.Model):
    list = models.ForeignKey(List, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
