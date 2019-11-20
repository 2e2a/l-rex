import re
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Field, Fieldset, Layout, Submit, Button
from crispy_forms.bootstrap import StrictButton, FieldWithButtons, InlineField, FormActions
from django import forms

from apps.contrib import forms as crispy_forms
from apps.item import models as item_models
from apps.study import models as study_models

from . import models


class RandomizationForm(crispy_forms.CrispyForm):
    randomization = forms.ChoiceField(choices=models.QuestionnaireBlock.RANDOMIZATION_TYPE, label='')

    def __init__(self, *args, **kwargs):
        randomization = kwargs.pop('randomization', None)
        super().__init__(*args, **kwargs)
        if randomization:
            self.fields['randomization'].initial = randomization

    def init_helper(self):
        self.helper = FormHelper()
        self.helper.form_class = 'form-inline'
        self.helper.layout = Layout(
            FieldWithButtons(
                Field('randomization', css_class='form-control-sm'),
                Submit('generate', 'Generate', css_class='btn-primary btn-sm mx-1')
            )
        )


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


def questionnaire_block_formset_helper(has_exmaple_block=False):
    formset_helper = FormHelper()
    label = 'Item block {{ forloop.counter0 }}' if has_exmaple_block else 'Item block {{ forloop.counter }}'
    formset_helper.add_layout(Layout(Fieldset(label, None, 'instructions', 'randomization')))
    formset_helper.add_input(Submit('submit', 'Submit'))
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
    formset_helper.add_layout(Layout(Fieldset('Item block {{ forloop.counter }}', None, 'instructions')))
    formset_helper.add_input(Submit('submit', 'Submit'))
    formset_helper.add_input(Submit('save', 'Save', css_class='btn-secondary'))
    return formset_helper


class QuestionnaireUploadForm(crispy_forms.CSVUploadForm):
    file = forms.FileField(
        help_text='The CSV file must contain a column for the questionnaire number, materials title, item number and '
                  'condition. Valid column delimiters: colon, semicolon, comma, space, or tab.',
    )
    questionnaire_column = forms.IntegerField(
        initial=1,
        help_text='Specify which column contains the questionnaire number.',
    )
    items_column = forms.IntegerField(
        initial=3,
        help_text='Specify which column contains the questionnaire items.'
                  'Format: Comma separated list of <MaterialsTitle>-<Item>-<Condition> (e.g. Filler-1a,Exp-2b,...).'
    )
    item_lists_column = forms.IntegerField(
        initial=-1,
        help_text='Specify which column contains the questionnaire item lists.'
                  'Format: Comma separated list of <MaterialsTitle>-<ListNumber> (e.g. Filler-0,Exp-1,...).'
    )

    validator_int_columns = ['questionnaire_column']

    def __init__(self, *args, **kwargs):
        self.study = kwargs.pop('study')
        super().__init__(*args, **kwargs)

    @staticmethod
    def read_items(study, items_string):
        items = []
        error_msg = None
        item_strings = items_string.split(',')
        for item_string in item_strings:
            pattern = re.compile('(.*)-(\d+)(\D+)')
            match = pattern.match(item_string)
            if not match or len(match.groups()) != 3:
                error_msg = 'Not a valid item format "{}".'.format(item_string)
                break
            materials_title = match.group(1)
            item_num = match.group(2)
            item_cond = match.group(3)
            try:
                item = item_models.Item.objects.get(
                    materials__study=study,
                    materials__title=materials_title,
                    number=item_num,
                    condition=item_cond,
                )
                items.append(item)
            except item_models.Item.DoesNotExist:
                error_msg = 'Item {} does not exist.'.format(item_string)
                break
        if error_msg:
            raise forms.ValidationError(error_msg)
        return items

    @staticmethod
    def read_item_lists(study, list_string):
        lists = []
        error_msg = None
        list_strings = list_string.split(',')
        for list_string in list_strings:
            pattern = re.compile('(.*)-(\d+)')
            match = pattern.match(list_string)
            if not match or len(match.groups()) != 2:
                error_msg = 'Not a valid item list format "{}".'.format(list_string)
                break
            materials_title = match.group(1)
            list_num = match.group(2)
            try:
                item_list = item_models.ItemList.objects.get(
                    materials__study=study,
                    materials__title=materials_title,
                    number=list_num,
                )
                lists.append(item_list)
            except item_models.ItemList.DoesNotExist:
                error_msg = 'Item list {} does not exist.'.format(list_string)
                break
        if error_msg:
            raise forms.ValidationError(error_msg)
        return lists

    def check_upload_form(self, reader, cleaned_data):
        used_items = set()
        for row in reader:
            int(row[cleaned_data['questionnaire_column'] - 1])
            item_lists_col = cleaned_data['item_lists_column']
            items_string = row[cleaned_data['items_column'] - 1]
            used_items.update(self.read_items(self.study, items_string))
            if item_lists_col > 0:
                item_lists_string = row[item_lists_col - 1]
                self.read_item_lists(self.study, item_lists_string)
        if not len(used_items) == item_models.Item.objects.filter(materials__study=self.study).count():
            raise forms.ValidationError('Not all items used in questionnaires.')


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


class DemographicsFormsetForm(crispy_forms.CrispyModelForm):

    class Meta:
        model = models.DemographicValue
        fields = ['field', 'value']
        widgets = {
            'field': forms.HiddenInput(),
        }


def demographics_formset_factory(n_fields, extra=0):
    return forms.modelformset_factory(
        models.DemographicValue,
        form=DemographicsFormsetForm,
        min_num=n_fields,
        max_num=n_fields,
        extra=extra,
        validate_max=True,
    )


def demographics_formset_init(formset, fields):
    for field, form in zip(fields, formset):
        form.fields['field'].initial = field.pk
        form.fields['value'].label = field.name


def demographics_formset_helper(submit_label='Continue'):
    formset_helper = FormHelper()
    formset_helper.add_layout(
        Layout(
            Field('field'),
            Field('value'),
        ),
    )
    formset_helper.add_input(
        Submit('submit', submit_label),
    )
    return formset_helper


class RatingBaseForm(crispy_forms.CrispyModelForm):
    feedback = forms.CharField(
        max_length=5000,
        required=False,
        widget=forms.HiddenInput(),
        label='Feedback',
    )
    feedbacks_given = forms.CharField(
        required=False,
        widget=forms.HiddenInput(),
    )

    def handle_feedbacks(self, feedbacks_given, feedback=None):
        if feedback:
            feedbacks_given.append(feedback.pk)
            self['feedback'].initial = feedback.feedback
            self.fields['feedback'].widget = forms.Textarea()
            self.fields['feedback'].widget.attrs['readonly'] = True
        self['feedbacks_given'].initial = ','.join(str(f) for f in feedbacks_given)


class RatingForm(RatingBaseForm):
    optional_label_ignore_fields = ['comment', 'feedback']

    @property
    def submit_label(self):
        return self.study.continue_label

    class Meta:
        model = models.Rating
        fields = ['scale_value', 'comment', 'feedback', 'feedbacks_given']

    @property
    def custom_helper(self):
        helper = FormHelper()
        helper.add_layout(
            Layout(
                Field('scale_value', template='lrex_trial/ratings_scale_value_field.html'),
                Field('comment'),
                Field('feedback'),
                Field('feedbacks_given'),
            ),
        )
        return helper

    def __init__(self, *args, **kwargs):
        self.study = kwargs.pop('study')
        question = kwargs.pop('question')
        questionnaire_item = kwargs.pop('questionnaire_item')
        item_question = kwargs.pop('item_question', None)
        super().__init__(*args, **kwargs)
        self.fields['scale_value'].empty_label = None
        self.fields['scale_value'].label = question.question
        self.fields['scale_value'].help_text = question.legend
        self.fields['scale_value'].queryset = study_models.ScaleValue.objects.filter(question=question)
        self.fields['scale_value'].error_messages['required'] = self.study.answer_question_message
        if item_question:
            if item_question.question: self.fields['scale_value'].label = item_question.question
            if item_question.legend: self.fields['scale_value'].help_text = item_question.legend
            if item_question.scale_labels:
                custom_choices = []
                item_labels = item_question.scale_labels.split(',')
                for (pk, _ ), custom_label in zip(self.fields['scale_value'].choices, item_labels):
                    custom_choices.append((pk, custom_label))
                self.fields['scale_value'].choices = custom_choices
        if question.randomize_scale:
            custom_choices = []
            initial_choices = [(pk, label) for pk, label in self.fields['scale_value'].choices]
            for scale_num in questionnaire_item.question_property(question.number).scale_order.split(','):
                custom_choices.append(initial_choices[int(scale_num)])
            self.fields['scale_value'].choices = custom_choices
        if question.rating_comment == question.RATING_COMMENT_NONE:
            self.fields['comment'].widget = forms.HiddenInput()
        elif question.rating_comment == question.RATING_COMMENT_REQUIRED:
            self.fields['comment'].label = self.study.comment_label
            self.fields['comment'].required = True
        else:
            self.fields['comment'].label = '{} ({})'.format(self.study.comment_label, self.study.optional_label)


class RatingFormsetForm(RatingBaseForm):
    optional_label_ignore_fields = ['comment', 'feedback']
    class Meta:
        model = models.Rating
        fields = ['question', 'scale_value', 'feedback', 'comment', 'feedbacks_given']
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


def ratingformset_init(ratingformset, questions, item_questions, questionnaire_item,
                       pseudo_randomize_question_order=False):

    def _get_item_question(num, item_questions):
        for item_question in item_questions:
            if item_question.number == num:
                return item_question

    def _get_reordered_questions_random(questions, question_order):
        reordered_questions = []
        for question_num in question_order.split(','):
            reordered_questions.append(questions[int(question_num)])
        return reordered_questions

    if pseudo_randomize_question_order:
        ordered_questions = _get_reordered_questions_random(questions, questionnaire_item.question_order)
    else:
        ordered_questions = questions
    for question, form in zip(ordered_questions, ratingformset):
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

        if question.rating_comment == question.RATING_COMMENT_NONE:
            form.fields['comment'].widget = forms.HiddenInput()
        elif question.rating_comment == question.RATING_COMMENT_REQUIRED:
            form.fields['comment'].required = True
        else:
            form.fields['comment'].label = form.fields['comment'].label + ' (optional)'

        form.fields['feedback'].widget = forms.HiddenInput()
        form.fields['feedbacks_given'].widget = forms.HiddenInput()


def ratingformset_handle_feedbacks(ratingformset, feedbacks):
    show_feedback = False
    for form, feedbacks_given, feedback in feedbacks:
        show_feedback = True
        ratingformset[form].handle_feedbacks(feedbacks_given, feedback=feedback)
    return show_feedback


def rating_formset_helper(submit_label='Continue'):
    formset_helper = FormHelper()
    formset_helper.add_layout(
        Layout(
            Field('scale_value', template='lrex_trial/ratings_scale_value_field.html'),
            Field('feedback'),
            Field('comment'),
            Field('feedbacks_given'),
        ),
    )
    formset_helper.add_input(
        Submit('submit', submit_label),
    )
    return formset_helper
