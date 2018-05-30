import csv
from django.urls import reverse
from django.db import models
from django.utils.text import slugify

from apps.item import models as item_models
from apps.trial import models as trial_models


class Experiment(models.Model):
    title = models.CharField(
        max_length=200,
        help_text='TODO',
        unique=True,
    )
    slug = models.SlugField(unique=True)
    study = models.ForeignKey(
        'lrex_study.Study',
        on_delete=models.CASCADE
    )
    PROGRESS_EXP_CREATED = '03ec'
    PROGRESS_EXP_ITEMS_CREATED = '03ic'
    PROGRESS_EXP_ITEMS_VALIDATED = '04iv'
    PROGRESS_EXP_LISTS_CREATED = '05lc'
    PROGRESS = (
        (PROGRESS_EXP_CREATED, 'Create an experiment'),
        (PROGRESS_EXP_ITEMS_CREATED, 'Create or upload experiment items'),
        (PROGRESS_EXP_ITEMS_VALIDATED, 'Validate the experiment items consistency'),
        (PROGRESS_EXP_LISTS_CREATED, 'Generate item lists'),
    )
    progress = models.CharField(
        max_length=4,
        choices=PROGRESS,
        default=PROGRESS_EXP_CREATED,
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

    def validate_items(self):
        conditions = []
        items = self.item_set.all()
        if len(items) == 0:
            raise AssertionError('No items.')

        for item in items:
            if item.condition not in conditions:
                conditions.append(item.condition)
            else:
                break

        condition_count = len(conditions)
        if len(items) % condition_count != 0:
            raise AssertionError('Number of items is not a multiple of the number of conditions.')

        item_number = 0
        for i, item in enumerate(items):
            if hasattr(item, 'textitem'):
                if not item.textitem.text:
                    raise AssertionError('Item {} has no text.'.format(item))
            elif hasattr(item, 'audiolinkitem'):
                if not item.audiolinkitem.url:
                    raise AssertionError('Item {} has no URL.'.format(item))

            if i % condition_count == 0:
                item_number += 1
            if item.number != item_number or item.condition != conditions[i % condition_count]:
                raise AssertionError('Items invalid. Item {} was not expected.'.format(item))

        return None

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
        ratings = trial_models.Rating.objects.filter(
            trial_item__item__experiment=self
        )
        for rating in ratings:
            row = {}
            item = rating.trial_item.item

            row['subject'] = rating.trial_item.trial.id
            row['item'] = item.number
            row['condition'] = item.condition
            row['rating'] = rating.scale_value.number
            if hasattr(item, 'textitem'):
                row['text'] = item.textitem.text

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
                aggregated_row['ratings'][row['rating'] - 1] += 1
            else:
                for aggregated_column in columns:
                    row[aggregated_column] = ''
                row['rating_count'] = 1
                row['ratings'] = [0.0] * len(self.study.scalevalue_set.all())
                row['ratings'][row['rating'] - 1] = 1.0
                aggregated_results.append(row)

        for aggregated_row in aggregated_results:
            aggregated_row['ratings'] = list(map(lambda x: x/aggregated_row['rating_count'], aggregated_row['ratings']))

        aggregated_results_sorted = sorted(aggregated_results, key=lambda r: (r['subject'], r['item'], r['condition']))

        return aggregated_results_sorted

    def results_csv(self, fileobj):
        writer = csv.writer(fileobj)
        csv_row = ['Subject', 'item', 'Condition', 'Rating']
        if self.study.has_text_items:
            csv_row.append('Text')
        writer.writerow(csv_row)
        results = self.results()
        for row in results:
            csv_row = [row['subject'], row['item'], row['condition'], row['rating']]
            if self.study.has_text_items:
                csv_row.append(row['text'])
            writer.writerow(csv_row)

    @staticmethod
    def progress_description(progress):
        return dict(Experiment.PROGRESS)[progress]

    def progress_reached(self, progress):
        return self.progress >= progress

    def progress_url(self, progress):
        if progress == self.PROGRESS_EXP_ITEMS_CREATED:
            return reverse('items', args=[self.study, self])
        elif progress == self.PROGRESS_EXP_ITEMS_CREATED:
            return reverse('items', args=[self.study, self])
        elif progress == self.PROGRESS_EXP_ITEMS_VALIDATED:
            return reverse('items', args=[self.study, self])
        elif progress == self.PROGRESS_EXP_LISTS_CREATED:
            return reverse('itemlists', args=[self.study, self])
        return None

    def set_progress(self, progress):
        # USE IT
        self.progress = progress
        self.save()
        if self.study.progress != self.study.PROGRESS_STD_EXP_CREATED:
            self.study.set_progress(self.study.PROGRESS_STD_EXP_CREATED)


    def next_progress_steps(self, progress):
        if progress == self.PROGRESS_EXP_CREATED:
            return [ self.PROGRESS_EXP_ITEMS_CREATED ]
        elif progress == self.PROGRESS_EXP_ITEMS_CREATED:
            return [ self.PROGRESS_EXP_ITEMS_CREATED, self.PROGRESS_EXP_ITEMS_VALIDATED ]
        elif progress == self.PROGRESS_EXP_ITEMS_VALIDATED:
            return [ self.PROGRESS_EXP_LISTS_CREATED ]
        elif progress == self.PROGRESS_EXP_LISTS_CREATED:
            return []

    def next_steps(self):
        next_steps = []
        for next_step in self.next_progress_steps(self.progress):
            description = '{} [ {} ]'.format(self.progress_description(next_step), self)
            url = self.progress_url(next_step)
            next_steps.append(( description, url, ))
        return next_steps
