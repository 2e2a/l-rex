from django.urls import reverse
from django.db import models
from django.utils.text import slugify

from apps.item import models as item_models
from apps.response import models as response_models

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

    def compute_lists(self):
        self.list_set.all().delete()

        lists = []
        conditions = self.conditions
        condition_count = len(conditions)
        for i in range(condition_count):
            list = item_models.List.objects.create(number=i, experiment=self)
            lists.append(list)

        for i, item in enumerate(self.item_set.all()):
            shift  =  (i - (item.number - 1)) % condition_count
            list = lists[shift]
            item_models.ListItem.objects.create(list=list, item=item)


    def results_binary_response(self):
        result = []
        responses = response_models.UserBinaryResponse.objects.filter(
            user_trial_item__item__experiment=self
        )
        for item in self.item_set.all():
            total_count = 0
            yes_count = 0
            for response in responses:
                if response.user_trial_item.item == item:
                    total_count = total_count + 1
                    if response.yes:
                        yes_count = yes_count + 1
            yes_prc = 0.0
            no_prc = 0.0
            if total_count > 0:
                yes_prc = (100 * yes_count) / total_count
                no_prc = 100 - yes_prc
            result.append((item, total_count, yes_prc, no_prc))
        return result

