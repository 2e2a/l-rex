import copy
import csv
from collections import Counter
from enum import Enum
from itertools import groupby
from string import ascii_lowercase

from django.db import models
from django.urls import reverse
from django.utils.functional import cached_property

from apps.contrib import csv as contrib_csv
from apps.contrib.utils import slugify_unique, split_list_string
from apps.item import models as item_models
from apps.trial import models as trial_models


class MaterialsSteps(Enum):
    STEP_EXP_ITEMS_CREATE = 1
    STEP_EXP_ITEMS_VALIDATE = 2
    STEP_EXP_LISTS_GENERATE = 3


class Materials(models.Model):
    title = models.CharField(
        max_length=100,
        help_text='Give the materials a name.',
    )
    slug = models.SlugField(
        unique=True,
        max_length=220,
    )
    study = models.ForeignKey(
        'lrex_study.Study',
        on_delete=models.CASCADE,
        related_name='materials',
    )
    LIST_DISTRIBUTION_LATIN_SQUARE = 'latin-square'
    LIST_DISTRIBUTION_ALL_TO_ALL = 'all-to-all'
    LIST_DISTRIBUTION = (
        (LIST_DISTRIBUTION_LATIN_SQUARE, 'Latin-Square Distribution'),
        (LIST_DISTRIBUTION_ALL_TO_ALL, 'Show all conditions to all participants'),
    )
    item_list_distribution = models.CharField(
        max_length=16,
        choices=LIST_DISTRIBUTION,
        default=LIST_DISTRIBUTION_LATIN_SQUARE,
        help_text='How to distribute items across lists.',
    )
    is_filler = models.BooleanField(
        default=False,
        help_text='Mark the items of this materials as fillers. '
                  'This setting will be relevant if you choose to pseudo-randomize the questionnaire.',
    )
    is_example = models.BooleanField(
        default=False,
        help_text='Items will all be in block 0 (preceding items from all other materials).'
    )
    block = models.IntegerField(
        help_text='Items will all be in this block (-1 = no automatic block assignment).',
        default=-1,
    )

    items_validated = models.BooleanField(
        default=False,
    )

    class Meta:
        ordering = ['study', 'title']
        verbose_name_plural = 'Materials'

    def save(self, *args, **kwargs):
        new_slug = slugify_unique('{}-{}'.format(self.study.slug, self.title), Materials, self.pk)
        slug_changed = False
        if new_slug != self.slug:
            self.slug = new_slug
            slug_changed = True
        super().save(*args, **kwargs)
        if slug_changed:
            for item in self.items.all():
                item.save()

    @cached_property
    def items_sorted_by_block(self):
        items = self.items.all().order_by('number', 'condition')
        items = sorted(items, key=lambda x: x.materials_block)
        return items

    @cached_property
    def item_count(self):
        if self.items_validated:
            return int(self.items.count() / self.condition_count)
        return 0

    def item_pos(self, item):
        return (
                self.items.filter(number__lt=item.number).count() +
                self.items.filter(number=item.number, condition__lte=item.condition).count()
        )

    @cached_property
    def condition_count(self):
        return self.items.filter(number=1).count()

    @cached_property
    def auto_block(self):
        if self.is_example:
            return 0
        if self.block > 0:
            return self.block
        return None

    @cached_property
    def item_blocks(self):
        if self.auto_block is not None:
            item_blocks = [self.auto_block]
        else:
            item_blocks = set([item.block for item in self.items.all()])
        return sorted(item_blocks)

    @cached_property
    def has_lists(self):
        return self.lists.exists()

    @cached_property
    def is_complete(self):
        return self.has_lists

    def set_items_validated(self, valid):
        self.items_validated = valid
        self.save()

    def delete_feedbacks(self):
        item_models.ItemFeedback.objects.filter(item__materials=self).delete()

    def delete_lists(self):
        self.study.delete_questionnaires()
        self.lists.all().delete()

    def __str__(self):
        return self.title

    def _warn_items_string(self, items):
        WARN_ITEMS_MAX = 10
        items_string = ', '.join([str(item) for item in list(items)[:WARN_ITEMS_MAX]])
        if len(items) > WARN_ITEMS_MAX:
            items_string += ",..."
        return items_string

    def validate_items(self):
        warnings = []
        conditions = []
        self.set_items_validated(False)

        items = self.items.prefetch_related('materials', 'textitem', 'markdownitem', 'audiolinkitem', 'item_questions')
        items = list(items.all())
        if len(items) == 0:
            raise AssertionError('No items.')

        for item in items:
            if item.condition not in conditions:
                conditions.append(item.condition)
            else:
                break

        n_items = len(items)
        if self.item_list_distribution == self.LIST_DISTRIBUTION_LATIN_SQUARE:
            if n_items % self.condition_count != 0:
                msg = 'Number of stimuli is not a multiple of the number of conditions (stimuli: {}, conditions: {})'.format(
                    n_items,
                    ', '.join('"{}"'.format(condition) for condition in conditions)
                )
                raise AssertionError(msg)

        questions = list(self.study.questions.all())
        item_number = 0
        for i, item in enumerate(items):
            if self.study.has_text_items:
                if not item.textitem.text:
                    raise AssertionError('Item {} has no text.'.format(item))
            elif self.study.has_markdown_items:
                if not item.markdownitem.text:
                    raise AssertionError('Item {} has no text.'.format(item))
            elif self.study.has_audiolink_items:
                if not item.audiolinkitem.urls:
                    raise AssertionError('Item {} has no URLs.'.format(item))

            for validated_item in items[:i]:
                if validated_item.number == item.number and validated_item.condition == item.condition:
                    raise AssertionError('Duplicate item "{}".'.format(item))

            if i % self.condition_count == 0:
                item_number += 1
            condition_number = i % self.condition_count
            if (
                    item.number != item_number or
                    condition_number > len(conditions) or item.condition != conditions[condition_number]
            ):
                msg = (
                    'Item "{}" was not expected based on previous items. '
                    'Check whether item numbers/conditions are correct.'
                ).format(item)
                raise AssertionError(msg)

            for item_question in item.item_questions.all():
                if item_question.number >= len(questions):
                    raise AssertionError('For item question validation the study question(s) must be defined first.')
                if item_question.scale_labels and \
                        len(split_list_string(item_question.scale_labels)) !=  \
                        questions[item_question.number].scale_values.count():
                    msg = 'Scale of the item question "{}" does not match the study question {} ' \
                          'scale.'.format(item, item_question.number + 1)
                    raise AssertionError(msg)

        if self.study.has_text_items or self.study.has_markdown_items:
            if self.study.has_text_items:
                items_by_text = groupby(items, lambda x: x.textitem.text)
            else:
                items_by_text = groupby(items, lambda x: x.markdownitem.text)
            for _, items_with_same_text in items_by_text:
                items = list(items_with_same_text)
                if len(items) > 1:
                    warnings.append('Items {} have the same text.'.format(self._warn_items_string(items)))
        elif self.study.has_audiolink_items:
            item_links = []
            for item in items:
                item_links.extend([(url, item) for url in item.audiolinkitem.urls_list])
            items_by_link = groupby(item_links, lambda x: x[0])
            for _, items_with_same_link in items_by_link:
                item_list = [item_link[1] for item_link in items_with_same_link]
                if item_list:
                    items = set(item_list)
                    if len(items) > 1:
                        warnings.append('Items {} have the same URL.'.format(self._warn_items_string(items)))
                    item_counter = Counter(item_list)
                    duplicate_items = [item for item in item_counter if item_counter[item] > 1]
                    if duplicate_items:
                        warnings.append('Items {} use the same URL multiple times.'.format(self._warn_items_string(duplicate_items)))
        msg = 'Detected {} items with following conditions: {} (sum: {} stimuli).'.format(
            item_number,
            ', '.join('"{}"'.format(condition) for condition in conditions),
            n_items,
        )
        warnings.append(msg)
        self.items_validated = True
        self.save()
        self.create_item_lists()
        return warnings

    def pregenerate_items(self, n_items, n_conditions):
        from apps.item.models import AudioLinkItem, TextItem, MarkdownItem
        self.set_items_validated(False)
        self.delete_lists()
        for n_item in range(1, n_items + 1):
            for condition in ascii_lowercase[:n_conditions]:
                item_cls = None
                if self.study.has_text_items:
                    item_cls = TextItem
                elif self.study.has_markdown_items:
                    item_cls = MarkdownItem
                elif self.study.has_audiolink_items:
                    item_cls = AudioLinkItem
                item_cls.objects.create(
                    number=n_item,
                    condition=condition,
                    materials=self,
                )

    def create_item_lists(self):
        self.lists.all().delete()
        item_lists = []
        if self.item_list_distribution == self.LIST_DISTRIBUTION_LATIN_SQUARE:
            for i in range(self.condition_count):
                item_list = item_models.ItemList(
                    materials=self,
                    number=i,
                )
                item_lists.append(item_list)
            item_models.ItemList.objects.bulk_create(item_lists)
            items_by_list = {item_list: [] for item_list in item_lists}
            for i, item in enumerate(self.items.all()):
                shift = (i - (item.number - 1)) % self.condition_count
                item_list = item_lists[shift]
                items_by_list[item_list].append(item)
            for item_list, items in items_by_list.items():
                item_list.items.set(items)
        elif self.item_list_distribution == self.LIST_DISTRIBUTION_ALL_TO_ALL:
            item_list = item_models.ItemList.objects.create(materials=self)
            item_list.items.set(list(self.items_sorted_by_block))

    def results(self):
        ratings = trial_models.Rating.objects.filter(
            questionnaire_item__item__materials=self,
        ).prefetch_related(
            'scale_value',
            'trial',
            'trial__questionnaire',
            'trial__questionnaire__study',
            'questionnaire_item',
            'questionnaire_item__item',
            'questionnaire_item__item__textitem',
            'questionnaire_item__item__audiolinkitem',
            'questionnaire_item__item__markdownitem',
            'questionnaire_item__question_properties',
        )
        has_question_with_random_scale = self.study.has_question_with_random_scale
        results = {}
        for rating in ratings:
            participant = rating.trial.number
            item = rating.questionnaire_item.item
            key = '{:03d}-{:03d}{}'.format(participant, item.number, item.condition)
            if rating.trial.is_test:
                key = 'test-' + key
            if key in results:
                row = results[key]
                row['questions'].append(rating.question)
                row['ratings'].append(rating.scale_value.number)
                row['labels'].append(rating.scale_value.label)
                row['comments'].append(rating.comment)
            else:
                row = {
                    'participant': participant,
                    'is_test_trial': 'yes' if rating.trial.is_test else 'no',
                    'item': item.number,
                    'condition': item.condition,
                    'position': rating.questionnaire_item.number + 1,
                    'content': item.content(self.study),
                    'questions': [rating.question],
                    'ratings': [rating.scale_value.number],
                    'labels': [rating.scale_value.label],
                    'comments': [rating.comment],
                }
                if self.study.pseudo_randomize_question_order:
                    row['question_order'] = rating.questionnaire_item.question_order_user
                if has_question_with_random_scale:
                    row['random_scale'] = '\n'.join(
                        q_property.question_scale_user
                        for q_property in rating.questionnaire_item.question_properties.all()
                    )
                results[key] = row
        results_sorted = [results[key] for key in sorted(results)]
        return results_sorted

    def _aggregated_results(self, results, group_function, key_function):
        grouped_results = {}
        for item, results in groupby(results, group_function):
            if item in grouped_results:
                grouped_results[item].extend(list(results))
            else:
                grouped_results[item] = list(results)
        questions = list(self.study.questions.prefetch_related('scale_values').all())
        aggregated_results = {}
        for results_for_item in grouped_results.values():
            rating_count = len(results_for_item)
            aggregated_result = copy.deepcopy(results_for_item[0])
            aggregated_result['scale_count'] = [None] * len(questions)
            for question in questions:
                aggregated_result['scale_count'][question.number] = {
                    scale_value.number: 0 for scale_value in question.scale_values.all()
                }
                for result in results_for_item:
                    aggregated_result['scale_count'][question.number][result['ratings'][question.number]] +=1

            aggregated_result['scale_ratings'] = {}
            aggregated_result['scale_ratings_flat'] = []
            for question_scale_count in aggregated_result['scale_count']:
                for scale, count in question_scale_count.items():
                    rating = count / rating_count
                    aggregated_result['scale_ratings'].update({scale: rating})
                    aggregated_result['scale_ratings_flat'].append(rating)

            aggregated_result['rating_count'] = rating_count
            aggregated_results.update({key_function(aggregated_result): aggregated_result})
        aggregated_results_sorted = [aggregated_results[key] for key in sorted(aggregated_results)]
        return aggregated_results_sorted

    def aggregated_results(self, columns):
        aggregated_results = []
        results = self.results()
        if columns == ['item', 'condition']:
            group_function = lambda result: str(result['item']) + result['condition']
            key_function = lambda result: '{:03d}-{}'.format(result['item'], result['condition'])
            aggregated_results = self._aggregated_results(results, group_function, key_function)
        elif columns == ['participant', 'condition']:
            group_function = lambda result: str(result['participant']) + result['condition']
            key_function = lambda result: '{:03d}-{}'.format(result['participant'], result['condition'])
            aggregated_results = self._aggregated_results(results, group_function, key_function)
        elif columns == ['condition']:
            group_function = lambda result: result['condition']
            key_function = lambda result: '{}'.format(result['condition'])
            aggregated_results = self._aggregated_results(results, group_function, key_function)
        return aggregated_results

    def items_csv_header(self, add_materials_column=False, zero_index=False):
        csv_row = ['materials'] if add_materials_column else []
        csv_row.extend(['item', 'condition', 'content', 'block'])
        if self.study.has_audiolink_items:
            csv_row.append('audio_description')
        for question in self.study.questions.all():
            question_number = question.number if zero_index else question.number + 1
            csv_row.append('question{}'.format(question_number))
            csv_row.append('scale{}'.format(question_number))
            csv_row.append('legend{}'.format(question_number))
        return csv_row

    def items_csv(self, fileobj, add_header=True, add_materials_column=False):
        writer = csv.writer(fileobj, delimiter=contrib_csv.DEFAULT_DELIMITER, quoting=contrib_csv.DEFAULT_QUOTING)
        if add_header:
            header = self.items_csv_header(add_materials_column=add_materials_column)
            writer.writerow(header)
        for item in self.items.all():
            csv_row = [self.title] if add_materials_column else []
            csv_row.extend([item.number, item.condition, item.content(self.study), item.block])
            if self.study.has_audiolink_items:
                csv_row.append(
                    item.audiolinkitem.description
                )
            for question in self.study.questions.all():
                if item.item_questions.filter(number=question.number).exists():
                    itemquestion = item.item_questions.get(number=question.number)
                    csv_row.extend([
                        itemquestion.question if itemquestion.question else '',
                        itemquestion.scale_labels if itemquestion.scale_labels else '',
                        itemquestion.legend if itemquestion.legend else '',
                    ])
                else:
                    csv_row.extend(['', '', ''])
            writer.writerow(csv_row)

    def items_from_csv(
            self, fileobj, has_materials_column=False, user_columns=None, detected_csv=contrib_csv.DEFAULT_DIALECT,
    ):
        questions = list(self.study.questions.all())
        item_questions = []
        self.items.all().delete()
        columns = contrib_csv.csv_columns(
            self.items_csv_header, user_columns=user_columns, add_materials_column=has_materials_column
        )
        custom_question_column = any('question{}'.format(question.number) in columns for question in questions)
        custom_scale_column = any('scale{}'.format(question.number) in columns for question in questions)
        reader = csv.reader(fileobj, delimiter=detected_csv['delimiter'], quoting=detected_csv['quoting'])
        if detected_csv['has_header']:
            next(reader)
        for row in reader:
            if not row:
                continue
            if has_materials_column and not row[columns['materials']] == self.title:
                continue
            if 'block' in columns and row[columns['block']]:
                block = int(row[columns['block']])
            else:
                block = 1

            item_fields = {
                'number': row[columns['item']],
                'condition': row[columns['condition']],
                'materials': self,
                'block': block,
            }
            if self.study.has_text_items:
                item_model = item_models.TextItem
                item_fields.update({
                    'text': row[columns['content']],
                })
            elif self.study.has_markdown_items:
                item_model = item_models.MarkdownItem
                item_fields.update({
                    'text': row[columns['content']],
                })
            else:
                item_model = item_models.AudioLinkItem
                item_fields.update({
                    'urls': row[columns['content']],
                })
                if 'audio_description' in columns:
                    item_fields['description'] = row[columns['audio_description']]
            item = item_model.objects.create(**item_fields)

            if custom_question_column or custom_scale_column:
                for question in questions:
                    question_column = 'question{}'.format(question.number)
                    scale_labels_column = 'scale{}'.format(question.number)
                    legend_column = 'legend{}'.format(question.number)
                    item_question_question = (
                        row[columns[question_column]] if question_column in columns else question.question
                    )
                    scale_labels = row[columns[scale_labels_column]] if scale_labels_column in columns else None
                    legend = row[columns[legend_column]] if legend_column in columns else None
                    item_question = item_models.ItemQuestion(
                        item=item,
                        number=question.number,
                        question=item_question_question,
                        scale_labels=scale_labels,
                        legend=legend,
                    )
                    item_questions.append(item_question)

        if item_questions:
            item_models.ItemQuestion.objects.bulk_create(item_questions)

    def item_feedbacks_csv_header(self, add_materials_column=False, **kwargs):
        csv_row = ['materials'] if add_materials_column else []
        csv_row.extend(['item_number', 'item_condition', 'question', 'scale_values', 'feedback'])
        return csv_row

    def item_feedbacks_csv(self, fileobj, add_header=True, add_materials_column=False):
        writer = csv.writer(fileobj, delimiter=contrib_csv.DEFAULT_DELIMITER, quoting=contrib_csv.DEFAULT_QUOTING)
        if add_header:
            header = self.item_feedbacks_csv_header()
            writer.writerow(header)
        for item_feedback in item_models.ItemFeedback.objects.filter(item__materials=self):
            csv_row = [self.title] if add_materials_column else []
            csv_row.extend([
                item_feedback.item.number,
                item_feedback.item.condition,
                item_feedback.question.number + 1,
                item_feedback.scale_values,
                item_feedback.feedback
            ])
            writer.writerow(csv_row)

    def item_feedbacks_from_csv(self, fileobj, has_materials_column=False, user_columns=None, detected_csv=contrib_csv.DEFAULT_DIALECT):
        self.delete_feedbacks()
        reader = csv.reader(fileobj, delimiter=detected_csv['delimiter'], quoting=detected_csv['quoting'])
        if detected_csv['has_header']:
            next(reader)
        columns = contrib_csv.csv_columns(
            self.item_feedbacks_csv_header, user_columns=user_columns, add_materials_column=has_materials_column
        )
        for row in reader:
            if not row:
                continue
            if has_materials_column and not row[columns['materials']] == self.title:
                continue
            item_number = row[columns['item_number']]
            item_condition = row[columns['item_condition']]
            item = self.items.get(number=item_number, condition=item_condition)
            question_num = int(row[columns['question']]) - 1
            question = self.study.get_question(question_num)
            scale_values = row[columns['scale_values']]
            feedback = row[columns['feedback']]
            item_models.ItemFeedback.objects.create(
                item=item,
                question=question,
                scale_values=scale_values,
                feedback=feedback
            )

    def itemlists_csv_header(self, add_materials_column=False, **kwargs):
        csv_row = ['materials'] if add_materials_column else []
        csv_row.extend(['list', 'items'])
        return csv_row

    def itemlists_csv(self, fileobj, add_header=True, add_materials_column=False):
        writer = csv.writer(fileobj, delimiter=contrib_csv.DEFAULT_DELIMITER, quoting=contrib_csv.DEFAULT_QUOTING)
        if add_header:
            header = self.itemlists_csv_header()
            writer.writerow(header)
        for item_list in self.lists.all():
            csv_row = [self.title] if add_materials_column else []
            csv_row.extend([
                item_list.number,
                ','.join([str(item) for item in item_list.items.all()])
            ])
            writer.writerow(csv_row)

    def itemlists_from_csv(self, fileobj, has_materials_column=False, user_columns=None, detected_csv=contrib_csv.DEFAULT_DIALECT):
        from apps.item.forms import ItemListUploadForm
        self.delete_lists()
        materials_items = list(self.items.all())
        reader = csv.reader(fileobj, delimiter=detected_csv['delimiter'], quoting=detected_csv['quoting'])
        if detected_csv['has_header']:
            next(reader)
        columns = contrib_csv.csv_columns(self.itemlists_csv_header, user_columns=user_columns, add_materials_column=has_materials_column)
        for row in reader:
            if not row:
                continue
            if has_materials_column and not row[columns['materials']] == self.title:
                continue
            list_num = row[columns['list']]
            items_string = row[columns['items']]
            items = ItemListUploadForm.read_items(items_string, materials_items=materials_items)
            itemlist = item_models.ItemList.objects.create(materials=self, number=list_num)
            itemlist.items.set(items)

    def results_csv_header(self):
        csv_row = ['materials', 'participant', 'is_test_trial', 'item', 'condition', 'position']
        if self.study.pseudo_randomize_question_order:
            csv_row.append('question order')
        if self.study.has_question_with_random_scale:
            csv_row.append('random scale')
        for question in self.study.questions.all():
            csv_row.append('rating{}'.format(question.number + 1))
        if self.study.has_question_rating_comments:
            for question in self.study.questions.all():
                csv_row.append('comment{}'.format(question.number + 1))
        csv_row.append('content')
        return csv_row

    def results_csv(self, fileobj):
        writer = csv.writer(fileobj, delimiter=contrib_csv.DEFAULT_DELIMITER, quoting=contrib_csv.DEFAULT_QUOTING)
        results = self.results()
        for result in results:
            csv_row = [
                self.title, result['participant'], result['is_test_trial'], result['item'], result['condition'],
                result['position']
            ]
            if self.study.pseudo_randomize_question_order:
                csv_row.append(result['question_order'])
            if self.study.has_question_with_random_scale:
                csv_row.append(result['random_scale'])
            for rating in result['labels']:
                csv_row.append(rating)
            if self.study.has_question_rating_comments:
                for comment in result['comments']:
                    csv_row.append(comment if comment else '')
            csv_row.append(result['content'])
            writer.writerow(csv_row)

    STEP_DESCRIPTION = {
        MaterialsSteps.STEP_EXP_ITEMS_CREATE: 'create or upload items',
        MaterialsSteps.STEP_EXP_ITEMS_VALIDATE: 'validate consistency of the items',
        MaterialsSteps.STEP_EXP_LISTS_GENERATE: 'generate item lists',
    }

    def step_url(self, step):
        if step == MaterialsSteps.STEP_EXP_ITEMS_CREATE:
            return reverse('items', args=[self.slug])
        if step == MaterialsSteps.STEP_EXP_ITEMS_VALIDATE:
            return reverse('items', args=[self.slug])
        if step == MaterialsSteps.STEP_EXP_LISTS_GENERATE:
            return reverse('itemlists', args=[self.slug])

    def _append_step_info(self, steps, step):
        steps.append((self.STEP_DESCRIPTION[step], self.step_url(step)))

    def next_steps(self):
        next_steps = []
        if not self.items.exists():
            self._append_step_info(next_steps, MaterialsSteps.STEP_EXP_ITEMS_CREATE)
        if self.items.exists() and not self.items_validated:
            self._append_step_info(next_steps, MaterialsSteps.STEP_EXP_ITEMS_VALIDATE)
        if self.items_validated and not self.lists.exists():
            self._append_step_info(next_steps, MaterialsSteps.STEP_EXP_LISTS_GENERATE)
        return {'Materials: {}'.format(self.title): next_steps}
