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
            row = {}

            subject = trials_list.index(rating.trial_item.trial) + 1
            row['subject'] = subject

            item = rating.trial_item.item
            row['item'] = item.number
            row['condition'] = item.condition
            row['text'] =  item.textitem.text

            row['rating_count'] = 1

            values = []
            for scale_value in self.study.scalevalue_set.all():
                if rating.scale_value == scale_value:
                    values.append(1.0)
                else:
                    values.append(0.0)
            row['values'] = values

            results.append(row)

        results_sorted = sorted(results, key=lambda r: (r['subject'], r['item'], r['condition']))
        return results_sorted

    def _aggregation_columns(self):
        return ['subject', 'item', 'condition']

    def _matching_row(self, row, aggregated_results, columns):
        match = -1
        for i, result_row in enumerate(aggregated_results):
            match = i
            colums_left = list(set(self._aggregation_columns())-set(columns))
            for col in colums_left:
                if result_row[col] != row[col]:
                    match = -1
                    break
            if match >= 0:
                break
        return match

    def aggregate(self, results, columns):
        aggregated_results = []
        for row in results:
            matching_row = self._matching_row(row, aggregated_results, columns)
            if matching_row >= 0:
                aggregated_row = aggregated_results[matching_row]
                aggregated_row['rating_count'] += 1
                aggregated_row['values'] = [x + y for x, y in zip(aggregated_row['values'], row['values'])]
            else:
                for aggregated_column in columns:
                    row[aggregated_column] = ''
                if 'item' in columns or 'condition' in columns:
                    row['text'] = ''
                aggregated_results.append(row)

        for aggregated_row in aggregated_results:
            aggregated_row['values'] = list(map(lambda x: x/aggregated_row['rating_count'], aggregated_row['values']))

        aggregated_results_sorted = sorted(aggregated_results, key=lambda r: (r['subject'], r['item'], r['condition']))

        return aggregated_results_sorted
