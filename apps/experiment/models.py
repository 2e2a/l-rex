import csv
from django.db import models
from django.urls import reverse
from django.utils.functional import cached_property

from apps.contrib.utils import slugify_unique
from apps.item import models as item_models
from apps.study import models as study_models
from apps.trial import models as trial_models


class Experiment(models.Model):
    title = models.CharField(
        max_length=200,
        help_text='Give your experiment a name.',
    )
    slug = models.SlugField(unique=True)
    study = models.ForeignKey(
        'lrex_study.Study',
        on_delete=models.CASCADE
    )
    is_filler = models.BooleanField(
        default=False,
        help_text='Mark the items of this experiment as fillers. '
                  'This setting will be relevant if you choose to pseudo-randomize the questionnaire.',
    )
    PROGRESS_EXP_CREATED = '21-exp-crt'
    PROGRESS_EXP_ITEMS_CREATED = '22-exp-itm-crt'
    PROGRESS_EXP_ITEMS_VALIDATED = '23-exp-itm-vld'
    PROGRESS_EXP_LISTS_CREATED = '24-exp-lst-gen'
    PROGRESS = (
        (PROGRESS_EXP_CREATED, 'Create an experiment'),
        (PROGRESS_EXP_ITEMS_CREATED, 'Create or upload experiment items'),
        (PROGRESS_EXP_ITEMS_VALIDATED, 'Validate consistency of the items'),
        (PROGRESS_EXP_LISTS_CREATED, 'Generate item lists'),
    )
    progress = models.CharField(
        max_length=16,
        choices=PROGRESS,
        default=PROGRESS_EXP_CREATED,
    )

    def save(self, *args, **kwargs):
        slug = '{}--{}'.format(self.study.slug, self.title)
        self.slug = slugify_unique(slug, Experiment, self.id)
        return super().save(*args, **kwargs)

    @cached_property
    def items(self):
        return self.item_set.all()

    @cached_property
    def conditions(self):
        items = self.item_set.filter(number=1)
        conditions = [item.condition for item in items]
        return conditions

    def __str__(self):
        return self.slug

    def get_absolute_url(self):
        return reverse('experiment', args=[self.slug])

    def validate_items(self):
        conditions = []
        items = self.item_set.all().order_by('number', 'condition')
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

    def compute_item_lists(self, distribute=True):
        self.itemlist_set.all().delete()

        item_lists = []
        if distribute:
            conditions = self.conditions
            condition_count = len(conditions)
            for _ in range(condition_count):
                item_list = item_models.ItemList.objects.create(experiment=self)
                item_lists.append(item_list)

            for i, item in enumerate(self.item_set.all().order_by('number', 'condition')):
                shift =  (i - (item.number - 1)) % condition_count
                item_list = item_lists[shift]
                item_list.items.add(item)
        else:
            item_list = item_models.ItemList.objects.create(experiment=self)
            items = list(self.item_set.all())
            item_list.items.add(*items)

    def results(self):
        results = []
        ratings = trial_models.Rating.objects.filter(
            questionnaire_item__item__experiment=self
        )
        if not self.study.require_participant_id:
            trials =  list(trial_models.Trial.objects.filter(
                questionnaire__study=self.study
            ))
        scale_values = {}
        questions = {}
        for question in self.study.questions:
            for scale_value in question.scalevalue_set.all():
                scale_values.update({scale_value.id: scale_value})
            questions.update({question.id: question})
        for rating in ratings:
            row = {}
            item = rating.questionnaire_item.item
            scale_value = scale_values[rating.scale_value_id]
            question = questions[scale_value.question_id]
            trial = rating.trial
            row['subject'] = trial.subject_id if self.study.require_participant_id else trials.index(trial)
            row['item'] = item.number
            row['condition'] = item.condition
            row['question'] = question.num
            row['rating'] = scale_value.num
            row['label'] = scale_value.label
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
            for col in columns:
                if result_row[col] != row[col]:
                    match = -1
                    break
            if match >= 0:
                break
        return match

    def _question_scale_offset(self):
        question_scale_offset =  []
        offset = 0
        for question in self.study.questions:
            question_scale_offset.append(offset)
            offset += question.scalevalue_set.count()
        return question_scale_offset

    def aggregated_results(self, columns):
        aggregated_results = []
        results = self.results()
        scale_value_count = study_models.ScaleValue.objects.filter(question__study=self.study).count()
        question_scale_offset = self._question_scale_offset()
        columns_left = list(set(self._aggregation_columns())-set(columns))
        for row in results:
            matching_row = self._matching_row(row, aggregated_results, columns_left)
            if matching_row >= 0:
                aggregated_row = aggregated_results[matching_row]
                aggregated_row['rating_count'] += 1
                aggregated_row['ratings'][question_scale_offset[row['question'] - 1] + row['rating'] - 1] += 1
            else:
                for aggregated_column in columns:
                    row[aggregated_column] = ''
                row['rating_count'] = 1
                row['ratings'] = [0.0] * scale_value_count

                row['ratings'][question_scale_offset[row['question'] - 1] + row['rating'] - 1] = 1.0
                aggregated_results.append(row)

        num_questions = len(self.study.questions)
        for aggregated_row in aggregated_results:
            aggregated_row['rating_count'] = aggregated_row['rating_count'] / num_questions

            aggregated_row['ratings'] = \
                list(map(lambda x: round(x/aggregated_row['rating_count'], 2), aggregated_row['ratings']))

        aggregated_results_sorted = sorted(aggregated_results, key=lambda r: (r['subject'], r['item'], r['condition']))

        return aggregated_results_sorted

    def _result_lists_for_questions(self, results):
        aggregated_results = []

        for row in results:
            match = self._matching_row(row, aggregated_results, ['subject', 'item', 'condition'])
            if match >= 0:
                aggregated_results[match]['ratings'][row['question'] - 1] = row['label']
            else:
                new_row = {}
                n_questions = len(self.study.questions)
                for col in ['subject', 'item', 'condition']:
                    new_row[col] = row[col]
                if 'text' in row:
                    new_row['text'] =  row['text']
                new_row['ratings'] = [-1] * n_questions
                new_row['ratings'][row['question'] - 1] = row['label']
                aggregated_results.append(new_row)
        return aggregated_results


    def results_csv(self, fileobj):
        writer = csv.writer(fileobj)
        csv_row = ['subject', 'item', 'condition']
        for i, _ in enumerate(self.study.questions):
            csv_row.append('rating{}'.format(i))
        if self.study.has_text_items:
            csv_row.append('text')
        writer.writerow(csv_row)
        results = self.results()
        results = self._result_lists_for_questions(results)
        for row in results:
            csv_row = [row['subject'], row['item'], row['condition']]
            for rating in row['ratings']:
                csv_row.append(rating)
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
            return reverse('items', args=[self])
        elif progress == self.PROGRESS_EXP_ITEMS_CREATED:
            return reverse('items', args=[self])
        elif progress == self.PROGRESS_EXP_ITEMS_VALIDATED:
            return reverse('items', args=[self])
        elif progress == self.PROGRESS_EXP_LISTS_CREATED:
            return reverse('itemlists', args=[self])
        return None

    def set_progress(self, progress):
        self.progress = progress
        self.save()
        if progress == self.PROGRESS_EXP_LISTS_CREATED:
            self.study.set_progress(self.study.PROGRESS_STD_EXP_COMPLETED)
        elif self.study.progress != self.study.PROGRESS_STD_EXP_CREATED \
                and progress != self.PROGRESS_EXP_ITEMS_VALIDATED:
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
