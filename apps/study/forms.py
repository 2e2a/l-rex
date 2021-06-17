from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Field, Fieldset, HTML, Layout, Submit
from django import forms
from django.contrib.auth.models import User

from apps.contrib import forms as contrib_forms
from apps.contrib import utils

from . import models


class StudyFilterSortForm(contrib_forms.CrispyForm):
    SORT_BY_DATE = 'date'
    SORT_BY_NAME = 'name'
    SORT_BY_CHOICES = (
        (SORT_BY_DATE, 'date'),
        (SORT_BY_NAME, 'name'),
    )
    sort_by = forms.ChoiceField(choices=SORT_BY_CHOICES, label='')
    archived = forms.BooleanField(required=False)
    shared = forms.BooleanField(required=False)

    def __init__(self, *args, **kwargs):
        sort_by = kwargs.pop('sort_by')
        archived = kwargs.pop('archived')
        shared = kwargs.pop('shared')
        super().__init__(*args, **kwargs)
        self.fields['sort_by'].initial = sort_by
        self.fields['archived'].initial = archived
        self.fields['shared'].initial = shared

    def init_helper(self):
        self.helper = FormHelper()
        self.helper.add_layout(
            Layout(
                HTML('<div class="form-group mr-2 text-secondary">Sort by:</div>'),
                Div('sort_by', css_class='mr-2'),
                HTML('<div class="form-group mx-2 text-secondary">Show:</div>'),
                Div('archived', css_class='mr-2'),
                Div('shared', css_class='mr-2'),
            )
        )
        submit = Submit('submit', 'Update')
        submit.field_classes = 'btn btn-sm btn-outline-secondary'
        self.helper.add_input(submit)
        self.helper.form_class = 'form-row align-items-center px-2 pt-2'
        self.helper.form_method = 'GET'


class StudyForm(contrib_forms.CrispyModelForm):

    class Meta:
        model = models.Study
        fields = [
            'title',
            'item_type',
        ]
        widgets = {
            'item_type': forms.RadioSelect(),
        }


class StudySettingsForm(contrib_forms.CrispyModelForm):

    class Meta:
        model = models.Study
        fields = [
            'title',
            'item_type',
            'password',
            'participant_id',
            'end_date',
            'trial_limit',
            'use_blocks',
            'pseudo_randomize_question_order',
            'use_vertical_scale_layout',
            'enable_item_rating_feedback',
        ]
        widgets = {
            'item_type': forms.RadioSelect(),
            'participant_id': forms.RadioSelect(),
            'end_date': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        self.disable_itemtype = kwargs.pop('disable_itemtype', False)
        disable_question_order = kwargs.pop('disable_randomize_question_order', False)
        disable_use_blocks = kwargs.pop('disable_use_blocks', False)
        disable_feedback = kwargs.pop('disable_feedback', False)
        super().__init__(*args, **kwargs)
        if disable_question_order:
            contrib_forms.disable_form_field(self, 'pseudo_randomize_question_order')
        if disable_use_blocks:
            contrib_forms.disable_form_field(self, 'use_blocks')
        if disable_feedback:
            contrib_forms.disable_form_field(self, 'enable_item_rating_feedback')
        if self.disable_itemtype:
            contrib_forms.disable_form_field(self, 'item_type')

    @property
    def custom_helper(self):
        helper = FormHelper()
        helper.add_layout(
            Layout(
                Fieldset(
                    'Basic settings',
                    'title',
                    'item_type',
                    HTML('<hr>'),
                ),
                Fieldset(
                    'Restrictions on participation',
                    'password',
                    'participant_id',
                    'end_date',
                    'trial_limit',
                    HTML('<hr>'),
                ),
                Fieldset(
                    'Additional design features',
                    'use_blocks',
                    'pseudo_randomize_question_order',
                    'enable_item_rating_feedback',
                    HTML('<hr>'),
                ),
            )
        )
        return helper


class StudyLabelsForm(contrib_forms.CrispyModelForm):

    class Meta:
        model = models.Study
        fields = [
            'continue_label',
            'save_consent_form_label',
            'consent_form_label',
            'contact_label',
            'instructions_label',
            'block_instructions_label',
            'optional_label',
            'comment_label',
            'participation_id_label',
            'password_label',
            'field_required_message',
            'answer_questions_message',
            'feedback_message',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.study.has_question_rating_comments:
            self.fields['optional_label'].widget = forms.HiddenInput()
            self.fields['comment_label'].widget = forms.HiddenInput()
        if not self.study.enable_item_rating_feedback:
            self.fields['feedback_message'].widget = forms.HiddenInput()
        else:
            self.fields['answer_questions_message'].widget = forms.HiddenInput()
        if self.study.participant_id != self.study.PARTICIPANT_ID_RANDOM:
            self.fields['participation_id_label'].widget = forms.HiddenInput()
        if not self.study.password:
            self.fields['password_label'].widget = forms.HiddenInput()


class StudyFromArchiveForm(contrib_forms.CrispyForm):
    file = forms.FileField(
        help_text='Choose an L-Rex archive file (zip format) that you downloaded previously.',
        widget=forms.FileInput,
    )


class StudyNewFromArchiveForm(StudyFromArchiveForm):
    title = forms.CharField(
        max_length=100,
        help_text='Title of the new study.'
    )


class StudyCopyForm(contrib_forms.CrispyForm):
    title = forms.CharField(
        max_length=100,
        help_text='Title of the new study.'
    )


class StudyInstructionsForm(contrib_forms.CrispyModelForm):
    optional_label_ignore_fields = [
        'instructions',
    ]

    class Meta:
        model = models.Study
        fields = [
            'instructions',
            'short_instructions',
        ]

    def __init__(self, *args, **kwargs):
        instance = kwargs.get('instance', None)
        if instance and not instance.instructions:
            kwargs['initial'].update({
                'instructions': 'Please rate the following sentences on the scale.',
            })
        super().__init__(*args, **kwargs)


class StudyIntroForm(contrib_forms.CrispyModelForm):
    optional_label_ignore_fields = [
        'intro',
        'outro',
    ]

    class Meta:
        model = models.Study
        fields = [
            'intro',
            'outro',
        ]

    def __init__(self, *args, **kwargs):
        instance = kwargs.get('instance', None)
        if instance:
            if not instance.intro:
                kwargs['initial'].update({
                    'intro': 'Welcome to this study!',
                })
            if not instance.outro:
                kwargs['initial'].update({
                    'outro': 'Thank you for participating!',
                })
        super().__init__(*args, **kwargs)


class ArchiveForm(contrib_forms.CrispyModelForm):
    is_archived = forms.BooleanField(
        required=True,
        label='Please confirm that you have successfully downloaded and checked the archive file and want to proceed.'
    )
    submit_label = 'Archive study (delete all study data)'
    submit_css_class = 'btn-danger'

    class Meta:
        model = models.Study
        fields = [
            'is_archived',
        ]

    def clean_is_archived(self):
        is_archived = self.cleaned_data['is_archived']
        if not is_archived:
            raise forms.ValidationError('Please confirm before proceeding.')
        return is_archived


class ScaleLabelsListField(forms.CharField):

    def __init__(self, **kwargs):
        kwargs.update({
            'max_length': 10 * models.ScaleValue.LABEL_MAX_LENGTH,
            'required': True,
            'widget': forms.Textarea,
        })
        super().__init__(**kwargs)

    def validate(self, value):
        super().validate(value)
        value_list = utils.split_list_string(value)
        if not len(value_list) > 1:
            raise forms.ValidationError('At least two values must be entered.')
        if any(len(value) > models.ScaleValue.LABEL_MAX_LENGTH for value in value_list):
            raise forms.ValidationError(
                'A scale value is too long. Limit: {} characters.'.format(models.ScaleValue.LABEL_MAX_LENGTH)
            )


class QuestionForm(contrib_forms.CrispyModelForm):
    scale_labels = ScaleLabelsListField(
        help_text=(
            'Rating scale labels, separated by commas (e.g. "1,2,3,4,5"). '
            'If a label contains a comma itself, escape it with "\\" (e.g. "A,B,Can\'t decide\\, I like both").'
        ),
    )

    class Meta:
        model = models.Question
        fields = [
            'question',
            'scale_labels',
            'randomize_scale',
            'legend',
            'rating_comment',
        ]

    def __init__(self, *args, **kwargs):
        study = kwargs.pop('study')
        super().__init__(*args, **kwargs)
        self.fields['scale_labels'].initial = self.instance.get_scale_labels(multiline=True) if self.instance else None
        if study.has_questionnaires:
            self.fields['randomize_scale'].widget.attrs['readonly'] = True
            self.fields['randomize_scale'].widget.attrs['disabled'] = True


class QuestionFormsetFactory(contrib_forms.CrispyModelFormsetFactory):
    model = models.Question
    form = QuestionForm

    @staticmethod
    def get_layout(study=None):
        return Layout(
                Fieldset(
                    'Question {{ forloop.counter }}', None, 'question', 'scale_labels', 'randomize_scale', 'legend',
                    'rating_comment', 'DELETE',
                    HTML('<hr>'),
                ),
            )


class SharedWithForm(contrib_forms.CrispyForm):
    shared_with = forms.CharField(
        required=False,
        label='Shared with',
        help_text='Give other users access to the study. Enter comma-separated user names (e.g. "user1, user2").',
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['shared_with'].initial = ', '.join(user.username for user in self.study.shared_with.all())

    def clean_shared_with(self):
        shared_with = self.cleaned_data['shared_with']
        if shared_with:
            shared_with = shared_with.replace(' ', '')
            for username in shared_with.split(','):
                if not User.objects.filter(username=username).exists():
                    raise forms.ValidationError('No user with username {} registered'.format(username))
        return shared_with


class StudyContactForm(contrib_forms.CrispyModelForm):
    optional_label_ignore_fields = [
        'contact_name',
        'contact_email',
    ]

    class Meta:
        model = models.Study
        fields = [
            'contact_name',
            'contact_email',
            'contact_affiliation',
            'contact_details',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in ['contact_name', 'contact_email']:
            self.fields[field].required = True


class StudyConsentForm(contrib_forms.CrispyModelForm):
    optional_label_ignore_fields = [
        'consent_form_text',
        'consent_statement',
    ]

    class Meta:
        model = models.Study
        fields = [
            'consent_form_text',
            'consent_statement',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['consent_form_text'].required = True
        self.fields['consent_statement'].required = True


class DemographicFieldForm(contrib_forms.CrispyModelForm):

    class Meta:
        model = models.DemographicField
        fields = [
            'name',
        ]


class DemographicsFormsetFactory(contrib_forms.CrispyModelFormsetFactory):
    model = models.DemographicField
    form = DemographicFieldForm

    @staticmethod
    def get_layout(study=None):
        return Layout(
            Fieldset('Demographic field {{ forloop.counter }}', None, 'name', 'DELETE', HTML('<hr>'))
        )
