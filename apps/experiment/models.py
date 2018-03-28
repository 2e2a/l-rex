from django.urls import reverse
from django.db import models
from django.utils.text import slugify

from apps.item import models as item_models
from apps.trial import models as trial_models


class Experiment(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    study = models.ForeignKey(
        'lrex_study.Study',
        on_delete=models.CASCADE
    )

    def save(self, *args, **kwargs):
        self.slug = slugify(self.title)
        return super().save(*args, **kwargs)

    @property
    def conditions(self):
        items = self.item_set.filter(number=1)
        conditions = [item.condition for item in items]
        return conditions

    def __str__(self):
        return self.slug

    def get_absolute_url(self):
        return reverse('experiment', args=[self.study.slug, self.slug])

    def compute_item_lists(self):
        self.itemlist_set.all().delete()

        item_lists = []
        conditions = self.conditions
        condition_count = len(conditions)
        for i in range(condition_count):
            item_list = item_models.ItemList.objects.create(number=i, experiment=self)
            item_lists.append(item_list)

        for i, item in enumerate(self.item_set.all()):
            shift =  (i - (item.number - 1)) % condition_count
            item_list = item_lists[shift]
            item_list.items.add(item)

    def results(self):
        results = []

        trials_list = list(trial_models.Trial.objects.filter(
            questionnaire__study=self.study
        ))
        ratings = trial_models.Rating.objects.filter(
            trial_item__item__experiment=self
        )
        for rating in ratings:
            values = []

            subject = trials_list.index(rating.trial_item.trial) + 1
            values.append(subject)

            item = rating.trial_item.item
            values.append(item.number)
            values.append(item.condition)
            values.append(item.textitem.text)

            rating_count = 1
            values.append(rating_count)

            for scale_value in self.study.scalevalue_set.all():
                if rating.scale_value == scale_value:
                    values.append(1)
                else:
                    values.append(0)

            results.append(values)

        results_sorted = sorted(results, key=lambda r: r[0])
        return results_sorted
