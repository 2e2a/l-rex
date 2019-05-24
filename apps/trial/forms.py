import csv
from io import StringIO
from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML, Field, Fieldset, Layout, Submit
from django import forms

from apps.contrib import forms as crispy_forms
from apps.contrib import csv as contrib_csv
from apps.experiment import models as experiment_models
from apps.item import models as item_models
from apps.study import models as study_models

from . import models


class QuestionnaireBlockForm(forms.ModelForm):

    class Meta:
        model = models.QuestionnaireBlock
        fields = ['randomization']


def questionnaire_block_factory(n_blocks):
    return forms.modelformset_factory(
        models.QuestionnaireBlock,
        form=QuestionnaireBlockForm,
        min_num=n_blocks,
        max_num=n_blocks,
    )


def customize_randomization(questionnaireblock_formset, study):
    if not study.is_allowed_pseudo_randomization:
        for form in questionnaireblock_formset:
            randomization = form.fields.get('randomization')
            randomization.choices = [(k, v) for k,v in randomization.choices
                                     if k != models.QuestionnaireBlock.RANDOMIZATION_PSEUDO]


def questionnaire_block_formset_helper():
    formset_helper = FormHelper()
    formset_helper.add_layout(
        Layout(
            Fieldset('Item block {{ forloop.counter }}', None, 'instructions', 'randomization'),
        ),
    )
    formset_helper.add_input(
        Submit("submit", "Submit"),
    )
    return formset_helper


class QuestionnaireBlockUpdateForm(forms.ModelForm):

    class Meta:
        model = models.QuestionnaireBlock
        fields = ['instructions']


def questionnaire_block_update_factory(n_blocks):
    return forms.modelformset_factory(
        models.QuestionnaireBlock,
        form=QuestionnaireBlockUpdateForm,
        min_num=n_blocks,
        max_num=n_blocks,
    )


def questionnaire_block_update_formset_helper():
    formset_helper = FormHelper()
    formset_helper.add_layout(
        Layout(
            Fieldset('Item block {{ forloop.counter }}', None, 'instructions'),
        ),
    )
    formset_helper.add_input(
        Submit("submit", "Submit"),
    )
    return formset_helper


class UploadQuestionnaireForm(crispy_forms.CrispyForm):
    file = forms.FileField(
        help_text='The CSV file must contain a column for the questionnaire number, experiment title, item number and '
                  'condition. Valid column delimiters: colon, semicolon, comma, space, or tab.',
    )
    questionnaire_column = forms.IntegerField(
        initial=1,
        help_text='Specify which column contains the questionnaire number.',
    )
    experiment_column = forms.IntegerField(
        initial=2,
        help_text='Specify which column contains the experiment title.',
    )
    item_number_column = forms.IntegerField(
        initial=3,
        help_text='Specify which column contains the item number.',
    )
    item_condition_column = forms.IntegerField(
        initial=4,
        help_text='Specify which column contains the condition.',
    )

    def __init__(self, *args, **kwargs):
        self.study = kwargs.pop('study')
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        file = cleaned_data['file']
        cleaned_data = super().clean()
        data = contrib_csv.read_file(cleaned_data)
        sniff_data = contrib_csv.sniff(data)
        validator_int_columns = ['questionnaire_column', 'item_number_column']
        delimiter, quoting, has_header = contrib_csv.detect_dialect(sniff_data, cleaned_data, validator_int_columns)
        reader = csv.reader(StringIO(data), delimiter=delimiter, quoting=quoting)
        if has_header:
            next(reader)
        try:
            item_count = 0
            experiments = set()
            for row in reader:
                assert int(row[cleaned_data['questionnaire_column'] - 1])
                assert int(row[cleaned_data['item_number_column'] - 1])
                experiment_title = row[cleaned_data['experiment_column'] - 1]
                try:
                    experiment = self.study.experiment_set.get(title=experiment_title)
                except experiment_models.Experiment.DoesNotExist:
                    raise forms.ValidationError('Experiment with title "{}" does not exists.'.format(experiment_title))
                item_number = row[cleaned_data['item_number_column'] - 1]
                item_condition = row[cleaned_data['item_condition_column'] -1]
                if not experiment.item_set.filter(number=item_number, condition=item_condition).exists():
                    error = 'Item {}{} of "{}" is not defined.'.format(item_number, item_condition, experiment_title)
                    raise forms.ValidationError(error)
                item_count += 1
                experiments.add(experiment)
            contrib_csv.seek_file(cleaned_data)
            if not item_count == item_models.Item.objects.filter(experiment__in=experiments).count():
                raise forms.ValidationError('Not all items used in questionnaires.')
        except (ValueError, AssertionError):
            raise forms.ValidationError(
                'File: Unexpected format in line %(n_line)s.',
                code='invalid',
                params={'n_line': reader.line_num})
        return cleaned_data


class TrialForm(crispy_forms.CrispyModelForm):
    password = forms.CharField(
        max_length=200,
        widget=forms.PasswordInput,
        help_text='Provide a password (as instructed by the experimenter).',
    )
    optional_label_ignore_fields = ['subject_id']

    @property
    def submit_label(self):
        return self.study.continue_label

    class Meta:
        model = models.Trial
        fields = ['subject_id']

    @property
    def _test_subject_id(self):
        test_num = 1
        while True:
            test_subject_id = 'Test {}'.format(test_num)
            if not models.Trial.objects.filter(questionnaire__study=self.study, is_test=True, subject_id=test_subject_id).exists():
                break
            test_num += 1
        return test_subject_id

    def __init__(self, *args, **kwargs):
        is_test = kwargs.pop('is_test')
        self.study = kwargs.pop('study')
        super().__init__(*args, **kwargs)
        if is_test:
            self.fields['subject_id'].initial = self._test_subject_id
            self.fields['subject_id'].readonly = True
        if self.study.require_participant_id:
            self.fields['subject_id'].required = True
        else:
            self.fields['subject_id'].required = False
            self.fields['subject_id'].widget = forms.HiddenInput()
        if not self.study.password:
            self.fields['password'].required = False
            self.fields['password'].widget = forms.HiddenInput()

    def clean_password(self):
        password = self.cleaned_data['password']
        if password and password != self.study.password:
            raise forms.ValidationError('Invalid password.')
        return password


class RatingForm(crispy_forms.CrispyModelForm):

    @property
    def submit_label(self):
        return self.study.continue_label

    class Meta:
        model = models.Rating
        fields = ['scale_value']
        error_messages = {
            'scale_value': {
                'required': 'Please answer this question.',
            },
    }

    @property
    def custom_helper(self):
        helper = FormHelper()
        helper.add_layout(
            Layout(
                Field('scale_value', template='lrex_trial/ratings_scale_value_field.html'),
            ),
        )
        return helper

    def __init__(self, *args, **kwargs):
        self.study = kwargs.pop('study')
        question = kwargs.pop('question')
        item_question = kwargs.pop('item_question', None)
        super().__init__(*args, **kwargs)
        self.fields['scale_value'].empty_label = None
        self.fields['scale_value'].label = question.question
        self.fields['scale_value'].help_text = question.legend
        self.fields['scale_value'].queryset = study_models.ScaleValue.objects.filter(question=question)
        if item_question:
            if item_question.question: self.fields['scale_value'].label = item_question.question
            if item_question.legend: self.fields['scale_value'].help_text = item_question.legend
            if item_question.scale_labels:
                custom_choices = []
                item_labels = item_question.scale_labels.split(',')
                for (pk, _ ), custom_label in zip(self.fields['scale_value'].choices, item_labels):
                    custom_choices.append((pk, custom_label))
                self.fields['scale_value'].choices = custom_choices


class RatingFormsetForm(forms.ModelForm):

    class Meta:
        model = models.Rating
        fields = ['scale_value', 'question']
        widgets = {
            'question': forms.HiddenInput(),
            'scale_value': forms.RadioSelect(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['scale_value'].empty_label = None
        self.fields['scale_value'].required = False


def ratingformset_factory(n_questions=1):
    return forms.modelformset_factory(
        models.Rating,
        form=RatingFormsetForm,
        min_num=n_questions,
        max_num=n_questions,
        extra=0,
        validate_max=True,
    )


def customize_to_questions(ratingformset, questions, item_questions):

    def _get_item_question(num, item_questions):
        for item_question in item_questions:
            if item_question.number == num:
                return item_question

    for question, form in zip(questions, ratingformset):
        item_question = _get_item_question(question.number, item_questions)
        form.fields['question'].initial = question.number
        scale_value = form.fields.get('scale_value')
        scale_value.queryset = scale_value.queryset.filter(question=question)
        scale_value.label = item_question.question if item_question else question.question
        scale_value.help_text = item_question.legend if item_question and item_question.legend else question.legend
        if item_question and item_question.scale_labels:
            custom_choices = []
            for (pk, _ ), custom_label in zip(scale_value.choices, item_question.scale_labels.split(',')):
                custom_choices.append((pk, custom_label))
            scale_value.choices = custom_choices


def rating_formset_helper(submit_label='Continue'):
    formset_helper = FormHelper()
    formset_helper.add_layout(
        Layout(
            Field('scale_value', template='lrex_trial/ratings_scale_value_field.html'),
        ),
    )
    formset_helper.add_input(
        Submit('submit', submit_label),
    )
    return formset_helper
