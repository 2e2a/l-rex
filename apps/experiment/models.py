import csv
from enum import Enum
from itertools import groupby
from django.db import models
from django.urls import reverse
from django.utils.functional import cached_property

from apps.contrib import csv as contrib_csv
from apps.contrib.utils import slugify_unique
from apps.item import models as item_models
from apps.study import models as study_models
from apps.trial import models as trial_models


class ExperimentSteps(Enum):
    STEP_EXP_ITEMS_CREATE = 1
    STEP_EXP_ITEMS_VALIDATE = 2
    STEP_EXP_LISTS_GENERATE = 3


class Experiment(models.Model):
    title = models.CharField(
        max_length=100,
        help_text='Give your experiment a name.',
    )
    slug = models.SlugField(
        unique=True,
        max_length=220,
    )
    study = models.ForeignKey(
        'lrex_study.Study',
        on_delete=models.CASCADE
    )
    is_filler = models.BooleanField(
        default=False,
        help_text='Mark the items of this experiment as fillers. '
                  'This setting will be relevant if you choose to pseudo-randomize the questionnaire.',
    )
    items_validated = models.BooleanField(
        default=False,
    )

    class Meta:
        ordering = ['study', 'title']

    def save(self, *args, **kwargs):
        slug = '{}--{}'.format(self.study.slug, self.title)
        new_slug = slugify_unique(slug, Experiment, self.id)
        if new_slug != self.slug:
            self.slug = slugify_unique(slug, Experiment, self.id)
            for item in self.items:
                item.save()
        return super().save(*args, **kwargs)

    @cached_property
    def items(self):
        return self.item_set.all()

    @cached_property
    def conditions(self):
        items = self.item_set.filter(number=1)
        conditions = [item.condition for item in items]
        return conditions

    @cached_property
    def item_blocks(self):
        item_bocks = set([item.block for item in self.items])
        return sorted(item_bocks)

    @cached_property
    def is_allowed_create_items(self):
        if not self.experiments:
            return False
        for experiment in self.experiments:
            if not experiment.is_complete:
                return False
        return True

    @cached_property
    def is_complete(self):
        return self.itemlist_set.exists()

    def set_items_validated(self, valid):
        self.items_validated = valid
        self.save()

    def delete_lists(self):
        self.study.delete_questionnaires()
        self.itemlist_set.all().delete()

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('experiment', args=[self.slug])

    def validate_items(self):
        warnings = []
        conditions = []
        self.set_items_validated(False)

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
            if self.study.has_text_items:
                if not item.textitem.text:
                    raise AssertionError('Item {} has no text.'.format(item))
            else:
                if not item.audiolinkitem.url:
                    raise AssertionError('Item {} has no URL.'.format(item))

            if i % condition_count == 0:
                item_number += 1
            if item.number != item_number or item.condition != conditions[i % condition_count]:
                msg = 'Item "{}" was not expected. Check whether item number/condition is correct.'.format(item)
                raise AssertionError(msg)

            questions = self.study.questions
            for item_question in item.itemquestion_set.all():
                if item_question.number >= len(questions):
                    raise AssertionError('For item question validation the study question(s) must be defined first.')
                if item_question.scale_labels and \
                        len(item_question.scale_labels.split(',')) !=  \
                        questions[item_question.number].scalevalue_set.count():
                    msg = 'Scale of the item question "{}" does not match the study question {} ' \
                          'scale.'.format(item, item_question.number)
                    raise AssertionError(msg)

        if self.study.has_text_items:
            items_by_text = groupby(items, lambda x: x.textitem.text)
            for _, items_with_same_text in items_by_text:
                items = list(items_with_same_text)
                if len(items) > 1:
                    warnings.append('Items {} have the same text.'.format(','.join([str(item) for item in items])))
        else:
            items_by_link = groupby(items, lambda x: x.audiolinkitem.url)
            for _, items_with_same_link in items_by_link:
                items = list(items_with_same_link)
                if len(items) > 1:
                    warnings.append('Items {} have the same URL.'.format(','.join([str(item) for item in items])))

        self.items_validated = True
        self.save()
        return warnings

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
            item_list.items.add(*list(self.items))

    def results(self):
        results = []
        ratings = trial_models.Rating.objects.filter(
            questionnaire_item__item__experiment=self
        ).prefetch_related(
            'trial', 'questionnaire_item',
        )
        for rating in ratings:
            row = {}
            item = rating.questionnaire_item.item
            row['subject'] = rating.trial.subject_id
            row['item'] = item.number
            row['condition'] = item.condition
            row['position'] = rating.questionnaire_item.number + 1
            row['question'] = rating.question
            row['rating'] = rating.scale_value.number
            row['label'] = rating.scale_value.label
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
                aggregated_row['ratings'][question_scale_offset[row['question']] + row['rating']] += 1
            else:
                for aggregated_column in columns:
                    row[aggregated_column] = ''
                row['rating_count'] = 1
                row['ratings'] = [0.0] * scale_value_count

                row['ratings'][question_scale_offset[row['question']] + row['rating']] = 1.0
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
                aggregated_results[match]['ratings'][row['question']] = row['label']
            else:
                new_row = {}
                n_questions = len(self.study.questions)
                for col in ['subject', 'item', 'condition', 'position']:
                    new_row[col] = row[col]
                if 'text' in row:
                    new_row['text'] =  row['text']
                new_row['ratings'] = [-1] * n_questions
                new_row['ratings'][row['question']] = row['label']
                aggregated_results.append(new_row)
        return aggregated_results

    def results_csv_header(self, add_experiment_column=False):
        csv_row = ['experiment'] if add_experiment_column else []
        csv_row.extend(['subject', 'item', 'condition', 'position'])
        for question in self.study.questions:
            csv_row.append('rating{}'.format(question.number + 1))
        if self.study.has_text_items:
            csv_row.append('text')
        return csv_row

    def results_csv(self, fileobj, add_header=True, add_experiment_column=False):
        writer = csv.writer(fileobj, delimiter=contrib_csv.DEFAULT_DELIMITER, quoting=contrib_csv.DEFAULT_QUOTING)
        if add_header:
            header = self.results_csv_header()
            writer.writerow(header)
        results = self.results()
        results = self._result_lists_for_questions(results)
        for row in results:
            csv_row = [self.title] if add_experiment_column else []
            csv_row.extend([row['subject'], row['item'], row['condition'], row['position']])
            for rating in row['ratings']:
                csv_row.append(rating)
            if self.study.has_text_items:
                csv_row.append(row['text'])
            writer.writerow(csv_row)

    STEP_DESCRIPTION = {
        ExperimentSteps.STEP_EXP_ITEMS_CREATE: 'Create or upload experiment items',
        ExperimentSteps.STEP_EXP_ITEMS_VALIDATE: 'Validate consistency of the items',
        ExperimentSteps.STEP_EXP_LISTS_GENERATE: 'Generate item lists',
    }

    def step_url(self, step):
        if step == ExperimentSteps.STEP_EXP_ITEMS_CREATE:
            return reverse('items', args=[self.slug])
        if step == ExperimentSteps.STEP_EXP_ITEMS_VALIDATE:
            return reverse('items', args=[self.slug])
        if step == ExperimentSteps.STEP_EXP_LISTS_GENERATE:
            return reverse('itemlists', args=[self.slug])

    def _append_step_info(self, steps, step):
        steps.append((self.STEP_DESCRIPTION[step], self.step_url(step)))

    def next_steps(self):
        next_steps = []
        if not self.items:
            self._append_step_info(next_steps, ExperimentSteps.STEP_EXP_ITEMS_CREATE)
        if self.items and not self.items_validated:
            self._append_step_info(next_steps, ExperimentSteps.STEP_EXP_ITEMS_VALIDATE)
        if self.items_validated and not self.itemlist_set.exists():
            self._append_step_info(next_steps, ExperimentSteps.STEP_EXP_LISTS_GENERATE)
        return next_steps
