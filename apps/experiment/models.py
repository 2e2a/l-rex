from django.core.urlresolvers import reverse
from django.db import models
from autoslug import AutoSlugField

from apps.item import models as item_models

class Experiment(models.Model):
    ITEM_TYPE = (
        ('txt', 'Text'),
    )
    title = models.CharField(max_length=200)
    slug = AutoSlugField(populate_from='title', unique=True)
    item_type = models.CharField(
        max_length=3,
        choices=ITEM_TYPE,
        default='txt',
    )
    setup = models.ForeignKey(
        'lrex_setup.Setup',
        on_delete=models.CASCADE
    )

    @property
    def conditions(self):
        item_model = self.item_model
        items = item_model.objects.filter(experiment=self, number=1)
        conditions = [item.condition for item in items]
        return conditions

    @property
    def item_model(self):
        return item_models.TextItem

    @property
    def text_items(self):
        return item_models.TextItem.objects.filter(experiment=self)

    @property
    def is_textitem(self):
        return self.item_type is 'txt'

    def __str__(self):
        return self.slug

    def get_absolute_url(self):
        return reverse('experiment', args=[self.setup.slug, self.slug])

    def compute_lists(self):
        item_models.List.objects.filter(experiment=self).delete()

        lists = []
        conditions = self.conditions
        condition_count = len(conditions)
        for i in range(condition_count):
            list = item_models.List.objects.create(number=i, experiment=self)
            lists.append(list)

        items = self.item_model.objects.filter(experiment=self)
        for i, item in enumerate(items):
            shift  =  (i - (item.number - 1)) % condition_count
            list = lists[shift]
            item_models.ListItem.objects.create(list=list, content_object=item)
