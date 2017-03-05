from django.conf import settings
from django.db import models
from autoslug import AutoSlugField


class Experiment(models.Model):
    ITEM_TYPE = (
        ('txt', 'Text'),
    )
    title = models.CharField(max_length=200)
    slug = AutoSlugField(populate_from='title')
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    item_type = models.CharField(
        max_length=3,
        choices=ITEM_TYPE,
        default='txt',
    )

    def text_items(self):
        return TextItem.objects.filter(experiment=self)

    def is_textitem(self):
        return self.item_type is 'txt'

    def __str__(self):
        return self.slug


class Item(models.Model):
    number = models.IntegerField()
    condition = models.CharField(max_length=8)
    experiment = models.ForeignKey(Experiment, on_delete=models.CASCADE)

    class Meta:
        abstract = True

    def __str__(self):
        return '{}-{}-{}'.format(self.experiment, self.number, self.condition)


class TextItem(Item):
    text = models.TextField(max_length=1024)
