import re
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Field, Fieldset, HTML, Layout, Submit, Button
from crispy_forms.bootstrap import FieldWithButtons, InlineField
from django import forms

from apps.contrib import forms as contrib_forms
from apps.contrib.utils import split_list_string
from apps.item import models as item_models

from . import models


class RandomizationForm(contrib_forms.CrispyForm):
    randomization = forms.ChoiceField(
        choices=models.QuestionnaireBlock.RANDOMIZATION_BASE,
        initial=models.QuestionnaireBlock.RANDOMIZATION_TRUE,
        label='',
    )

    def __init__(self, *args, **kwargs):
        randomization = kwargs.pop('randomization', None)
        allow_pseudo_random = kwargs.pop('allow_pseudo_random', False)
        super().__init__(*args, **kwargs)
        if allow_pseudo_random:
            self.fields['randomization'].choices = models.QuestionnaireBlock.RANDOMIZATION_TYPE
        if randomization:
            self.fields['randomization'].initial = randomization
        elif allow_pseudo_random:
            self.fields['randomization'].initial = models.QuestionnaireBlock.RANDOMIZATION_PSEUDO
        else:
            self.fields['randomization'].initial = models.QuestionnaireBlock.RANDOMIZATION_TRUE

    def init_helper(self):
        self.helper = FormHelper()
        self.helper.form_class = 'form-inline'
        self.helper.layout = Layout(
            FieldWithButtons(
                Field('randomization', css_class='form-control-sm mt-1'),
                Submit('generate', 'Generate', css_class='btn-primary btn-sm mx-1 mt-1')
            )
        )


class QuestionnaireGenerateForm(contrib_forms.CrispyModelForm):
    optional_label_ignore_fields = ('randomization',)

    class Meta:
        model = models.QuestionnaireBlock
        fields = ['randomization']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.study.is_allowed_pseudo_randomization:
            self.fields.get('randomization').choices = [
                (k, v) for k,v in self.fields.get('randomization').choices
                if k != models.QuestionnaireBlock.RANDOMIZATION_PSEUDO
            ]


class QuestionnaireGenerateFormsetFactory(contrib_forms.CrispyModelFormsetFactory):
    model = models.QuestionnaireBlock
    form = QuestionnaireGenerateForm

    @staticmethod
    def get_layout(study=None):
        label = 'Item block {{ forloop.counter0 }}' if study.has_exmaples else 'Item block {{ forloop.counter }}'
        return Layout(
            Fieldset(
                label, None, 'randomization', 'DELETE', HTML('<hr>')
            ),
        )

    @classmethod
    def get_inputs(cls, study=None):
        return [
            Submit('submit', 'Submit'),
        ]


class QuestionnaireBlockUpdateForm(contrib_forms.CrispyModelForm):

    class Meta:
        model = models.QuestionnaireBlock
        fields = [
            'instructions',
            'short_instructions',
        ]


class QuestionnaireBlockFormsetFactory(contrib_forms.CrispyModelFormsetFactory):
    model = models.QuestionnaireBlock
    form = QuestionnaireBlockUpdateForm

    @staticmethod
    def get_layout(study=None):
        label = 'Item block {{ forloop.counter0 }}' if study.has_exmaples else 'Item block {{ forloop.counter }}'
        return Layout(
            Fieldset(label, None, 'instructions', 'short_instructions', HTML('<hr>')),
        )


class QuestionnaireUploadForm(contrib_forms.CSVUploadForm):
    file = forms.FileField(
        help_text='The CSV file must contain a column for the questionnaire number, materials title, item number and '
                  'condition. Valid column delimiters: colon, semicolon, comma, space, or tab.',
        widget=forms.FileInput,
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
        super().__init__(*args, **kwargs)

    @staticmethod
    def read_items(items_string, materials_titles, study_items):
        items = []
        item_strings = items_string.split(',')
        for item_string in item_strings:
            pattern = re.compile(r'(.*)-(\d+)(\D+)')
            match = pattern.match(item_string)
            if not match or len(match.groups()) != 3:
                raise forms.ValidationError('Not a valid item format "{}".'.format(item_string))
            materials_title = match.group(1)
            try:
                item_num = int(match.group(2))
                item_cond = match.group(3)
                item_match = None
            except ValueError:
                raise forms.ValidationError('Not a valid item format "{}".'.format(item_string))
            for item in study_items:
                if (
                        item.number == item_num and item.condition == item_cond
                        and materials_titles[item.materials_id] == materials_title
                ):
                    item_match = item
                    break
            if item_match:
                items.append(item_match)
            else:
                raise forms.ValidationError('Item {} does not exist.'.format(item_string))
        return items

    @staticmethod
    def read_item_lists(study, list_string, materials_titles, study_itemlists):
        lists = []
        list_strings = list_string.split(',')
        for list_string in list_strings:
            pattern = re.compile(r'(.*)-(\d+)')
            match = pattern.match(list_string)
            if not match or len(match.groups()) != 2:
                raise forms.ValidationError('Not a valid item list format "{}".'.format(list_string))
            try:
                materials_title = match.group(1)
                list_num = int(match.group(2))
            except ValueError:
                raise forms.ValidationError('Not a valid item list format "{}".'.format(list_string))
            list_match = None
            for item_list in study_itemlists:
                if item_list.number == list_num and materials_titles[item_list.materials_id] == materials_title:
                    list_match = item_list
                    break
            if list_match:
                lists.append(list_match)
            else:
                raise forms.ValidationError('Item list {} does not exist.'.format(list_string))
        return lists

    def check_upload_form(self, reader, cleaned_data):
        materials_titles = { materials.pk: materials.title for materials in self.materials.all()}
        study_items = list(item_models.Item.objects.filter(marials__study=self.study).all())
        for row in reader:
            int(row[cleaned_data['questionnaire_column'] - 1])
            item_lists_col = cleaned_data['item_lists_column']
            items_string = row[cleaned_data['items_column'] - 1]
            self.read_items(items_string, materials_titles, study_items)
            if item_lists_col > 0:
                item_lists_string = row[item_lists_col - 1]
                self.read_item_lists(self.study, item_lists_string, materials_titles, study_items)


class RequiredMessageFromStudyMixin:

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.error_messages['required'] = self.study.field_required_message


class ConsentForm(RequiredMessageFromStudyMixin, contrib_forms.CrispyForm):
    consent = forms.BooleanField()

    def __init__(self, *args, **kwargs):
        is_test = kwargs.pop('is_test')
        super().__init__(*args, **kwargs)
        self.fields['consent'].label = self.study.consent_statement

    def init_helper(self):
        super().init_helper()
        self.helper.add_input(
            Button(
                'print', self.study.save_consent_form_label, css_class='btn btn-secondary', onclick='window.print()'
            )
        )

    @property
    def submit_label(self):
        return self.study.continue_label


class TrialForm(RequiredMessageFromStudyMixin, contrib_forms.CrispyModelForm):
    password = forms.CharField(
        max_length=200,
        widget=forms.PasswordInput,
    )
    optional_label_ignore_fields = ['participant_id']

    @property
    def submit_label(self):
        return self.study.continue_label

    class Meta:
        model = models.Trial
        fields = ['participant_id']
        help_texts = {
            'password': None,
            'participant_id': None,
        }

    @property
    def _test_participant_id(self):
        test_num = 1
        while True:
            test_participant_id = 'Test {}'.format(test_num)
            if not models.Trial.objects.filter(questionnaire__study=self.study, is_test=True, participant_id=test_participant_id).exists():
                break
            test_num += 1
        return test_participant_id

    def __init__(self, *args, **kwargs):
        is_test = kwargs.pop('is_test')
        super().__init__(*args, **kwargs)
        self.fields['participant_id'].label = self.study.participation_id_label
        self.fields['password'].label = self.study.password_label
        if is_test:
            self.fields['participant_id'].initial = self._test_participant_id
            self.fields['participant_id'].readonly = True
        if self.study.participant_id == self.study.PARTICIPANT_ID_ENTER:
            self.fields['participant_id'].required = True
        else:
            self.fields['participant_id'].required = False
            self.fields['participant_id'].widget = forms.HiddenInput()
        if not self.study.password:
            self.fields['password'].required = False
            self.fields['password'].widget = forms.HiddenInput()

    def clean_password(self):
        password = self.cleaned_data['password']
        if password and password != self.study.password:
            raise forms.ValidationError('Invalid password.')
        return password


class DemographicsValueForm(RequiredMessageFromStudyMixin, contrib_forms.CrispyModelForm):

    class Meta:
        model = models.DemographicValue
        fields = ['value']

    def __init__(self, *args, **kwargs):
        demographics_value = kwargs.pop('demographics_value')
        is_test = kwargs.pop('is_test')
        super().__init__(*args, **kwargs)
        self.fields['value'].label = demographics_value.name


class DemographicsValueFormset(forms.BaseModelFormSet):

    def get_form_kwargs(self, index):
        kwargs = super().get_form_kwargs(index)
        study = kwargs.get('study')
        kwargs['demographics_value'] = study.demographics.get(number=index)
        return kwargs


class DemographicsValueFormsetFactory(contrib_forms.CrispyModelFormsetFactory):
    model = models.DemographicValue
    form = DemographicsValueForm

    @staticmethod
    def get_layout(study=None):
        return Layout('field', 'value')

    @classmethod
    def get_inputs(cls, study=None):
        return [
            Submit('submit', study.continue_label),
        ]


class RatingForm(RequiredMessageFromStudyMixin, contrib_forms.CrispyModelForm):
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
    optional_label_ignore_fields = ['comment', 'feedback']

    question = None
    feedbacks = None

    class Meta:
        model = models.Rating
        fields = ['question', 'scale_value', 'feedback', 'comment', 'feedbacks_given']
        widgets = {
            'question': forms.HiddenInput(),
            'scale_value': forms.RadioSelect(),
        }

    def __init__(self, *args, **kwargs):
        is_test = kwargs.pop('is_test')
        self.question = kwargs.pop('question')
        item_question = kwargs.pop('item_question')
        question_property = kwargs.pop('question_property')
        self.feedbacks = kwargs.pop('feedbacks')
        super().__init__(*args, **kwargs)
        self.fields['scale_value'].empty_label = None
        if self.question.rating_comment == self.question.RATING_COMMENT_NONE:
            self.fields['comment'].widget = forms.HiddenInput()
        elif self.question.rating_comment == self.question.RATING_COMMENT_REQUIRED:
            self.fields['comment'].label = self.study.comment_label
            self.fields['comment'].required = True
        else:
            self.fields['comment'].label = '{} ({})'.format(self.study.comment_label, self.study.optional_label)
        self.fields['question'].initial = self.question.number
        scale_value = self.fields.get('scale_value')
        scale_value.queryset = scale_value.queryset.filter(question=self.question)
        scale_value.label = item_question.question if item_question else self.question.question
        scale_value.help_text = item_question.legend if item_question and item_question.legend else self.question.legend
        choices = scale_value.choices
        if item_question and item_question.scale_labels:
            custom_choices = []
            for (pk, _), custom_label in zip(scale_value.choices, split_list_string(item_question.scale_labels)):
                custom_choices.append((pk, custom_label))
            choices = custom_choices
        if question_property and question_property.scale_order:
            reordered_choices = []
            for pos in question_property.scale_order.split(','):
                reordered_choices.append(list(choices)[int(pos)])
            choices = reordered_choices
        scale_value.choices = choices

    def clean(self):
        data = super().clean()
        scale_value = data.get('scale_value')
        if scale_value:
            feedbacks_given = data['feedbacks_given'].split(',')
            if self.feedbacks:
                feedbacks_for_scale = [
                    f for f in self.feedbacks
                    if f.question == self.question and str(f.pk) not in feedbacks_given and f.show_feedback(scale_value)
                ]
                if feedbacks_for_scale:
                    self.data = self.data.copy()
                    feedback_text = '\n'.join([f.feedback for f in feedbacks_for_scale])
                    self.data['form-{}-feedback'.format(self.question.number)] = feedback_text
                    self.fields['feedback'].widget = forms.Textarea()
                    self.fields['feedback'].widget.attrs['readonly'] = True
                    feedbacks_given += [str(f.pk) for f in feedbacks_for_scale]
                    self.data['form-{}-feedbacks_given'.format(self.question.number)] = ','.join(feedbacks_given)
                    raise forms.ValidationError({'feedbacks_given': []})

    def handle_feedbacks(self, feedbacks_given, feedback=None):
        if feedback:
            feedbacks_given.append(feedback.pk)
            self['feedback'].initial = feedback.feedback
            self.fields['feedback'].widget = forms.Textarea()
            #self.fields['feedback'].widget.attrs['readonly'] = True
        self['feedbacks_given'].initial = ','.join(str(f) for f in feedbacks_given)


class RatingFormset(forms.BaseModelFormSet):

    def get_form_kwargs(self, index):
        kwargs = super().get_form_kwargs(index)
        study = kwargs.get('study')
        questionnaire_item = kwargs.pop('questionnaire_item')
        kwargs.update({
            'question': study.questions.get(number=index),
            'question_property': questionnaire_item.question_properties.filter(number=index).first(),
            'item_question': questionnaire_item.item.item_questions.filter(number=index).first(),
            'feedbacks': list(questionnaire_item.item.item_feedback.all()),
        })
        #kwargs['demographics_value'] = study.demographics.get(number=index)
        return kwargs


class RatingFormsetFactory(contrib_forms.CrispyModelFormsetFactory):
    model = models.Rating
    form = RatingForm
    form_tag = False

    @staticmethod
    def get_layout(study=None):
        return Layout(
            Field('scale_value', template='lrex_trial/ratings_scale_value_field.html'),
            'feedback',
            'comment',
            'feedbacks_given',
        )
