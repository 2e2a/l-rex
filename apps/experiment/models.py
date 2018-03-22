from django.urls import reverse
from django.db import models
from django.utils.text import slugify

from apps.item import models as item_models
from apps.results import models as response_models
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
            list.items.add(item)

    def results(self):
        results = []

        user_trials_list = list(trial_models.UserTrial.objects.filter(
            trial__study=self.study
        ))
        user_responses = response_models.UserResponse.objects.filter(
            user_trial_item__item__experiment=self
        )
        for user_response in user_responses:
            values = []

            subject = user_trials_list.index(user_response.user_trial_item.user_trial) + 1
            values.append(subject)

            item = user_response.user_trial_item.item
            values.append(item.number)
            values.append(item.condition)
            values.append(item.textitem.text)

            result_count = 1
            values.append(result_count)

            for scale_value in self.study.scalevalue_set.all():
                if user_response.scale_value == scale_value:
                    values.append(1)
                else:
                    values.append(0)

            results.append(values)

        results_sorted = sorted(results, key=lambda r: r[0])
        return results_sorted
