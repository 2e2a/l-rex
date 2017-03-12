from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from autoslug import AutoSlugField


class Setup(models.Model):
    title = models.CharField(max_length=200)
    slug = AutoSlugField(populate_from='title')
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self):
        return self.slug

    def experiments(self):
        return Experiment.objects.filter(setup=self)


class Experiment(models.Model):
    ITEM_TYPE = (
        ('txt', 'Text'),
    )
    title = models.CharField(max_length=200)
    slug = AutoSlugField(populate_from='title')
    item_type = models.CharField(
        max_length=3,
        choices=ITEM_TYPE,
        default='txt',
    )
    setup = models.ForeignKey(Setup, on_delete=models.CASCADE)

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


class Response(models.Model):
    experiment = models.ForeignKey(Experiment, on_delete=models.CASCADE)
    question = models.CharField(max_length=200)
    legend = models.TextField(max_length=1024)

    class Meta:
        abstract = True

    def __str__(self):
        return '{}-response'.format(self.experiment)


class BinaryResponse(Response):
    yes = models.CharField(max_length=200)
    no = models.CharField(max_length=200)


class List(models.Model):
    number = models.IntegerField()
    experiment = models.ForeignKey(Experiment, on_delete=models.CASCADE)

    def __str__(self):
        return '{}-list-{}'.format(self.experiment, self.number)


class ListItem(models.Model):
    list = models.ForeignKey(List, on_delete=models.CASCADE)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')


