from crispy_forms.helper import FormHelper
from crispy_forms.layout import Fieldset, HTML, Layout, Submit
from django import forms
from django.contrib.auth.models import User

from apps.contrib import forms as contrib_forms

from . import models


class StudyForm(contrib_forms.CrispyModelForm):

    class Meta:
        model = models.Study
        fields = [
            'title',
            'item_type',
        ]


class StudySettingsForm(contrib_forms.CrispyModelForm):

    class Meta:
        model = models.Study
        fields = [
            'title',
            'item_type',
            'password',
            'require_participant_id',
            'end_date',
            'trial_limit',
            'use_blocks',
            'pseudo_randomize_question_order',
            'enable_item_rating_feedback',
        ]

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
                    'require_participant_id',
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


class StudyTranslationsForm(contrib_forms.CrispyModelForm):

    class Meta:
        model = models.Study
        fields = [
            'continue_label',
            'privacy_statement_label',
            'contact_label',
            'instructions_label',
            'block_instructions_label',
            'optional_label',
            'comment_label',
            'answer_question_message',
            'answer_questions_message',
            'feedback_message',
        ]

    def __init__(self, *args, **kwargs):
        study = kwargs.pop('study')
        super().__init__(*args, **kwargs)
        if not study.has_question_rating_comments:
            self.fields['optional_label'].widget = forms.HiddenInput()
            self.fields['comment_label'].widget = forms.HiddenInput()
        if not study.enable_item_rating_feedback:
            self.fields['feedback_message'].widget = forms.HiddenInput()
        if len(study.questions) > 1:
            self.fields['answer_question_message'].widget = forms.HiddenInput()
        else:
            self.fields['answer_questions_message'].widget = forms.HiddenInput()


class StudyFromArchiveForm(contrib_forms.CrispyForm):
    file = forms.FileField(
        help_text='An L-Rex archive file previously downloaded.'
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
        label='Please, confirm that you have successfully downloaded and checked the archive file and want to proceed.'
    )

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


class QuestionForm(contrib_forms.CrispyModelForm):
    scale_labels = contrib_forms.ListField(
        max_length=200,
        required=True,
        help_text='Rating scale labels, separated by commas (e.g. "1,2,3,4,5"). '
                  'If a label contains a comma itself, escape it with "\\" (e.g. "A,B,Can\'t decide\\, I like both").'
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


def question_formset_factory(n_questions, extra=0):
    return forms.modelformset_factory(
        models.Question,
        form=QuestionForm,
        min_num=n_questions,
        extra=extra,
    )


def initialize_with_questions(question_formset, questions):
    for question, form in zip(questions, question_formset):
        form['scale_labels'].initial = question.scale_labels


def question_formset_disable_fields(question_formset, **kwargs):
    disable_randomize_scales = kwargs.pop('disable_randomize_scale', False)
    for form in question_formset:
        if disable_randomize_scales:
            form.fields['randomize_scale'].widget.attrs['readonly'] = True
            form.fields['randomize_scale'].widget.attrs['disabled'] = True


def question_formset_helper():
    formset_helper = FormHelper()
    formset_helper.add_layout(
        Layout(
            Fieldset('Question {{ forloop.counter }}', None, 'question', 'scale_labels', 'randomize_scale', 'legend', 'rating_comment'),
        ),
    )
    formset_helper.add_input(Submit('submit', 'Submit'))
    formset_helper.add_input(Submit('save', 'Save', css_class='btn-secondary'))
    formset_helper.add_input(Submit('add', 'Add', css_class='btn-secondary'))
    formset_helper.add_input(Submit('delete', 'Delete last', css_class='btn-danger'))
    return formset_helper


class SharedWithForm(contrib_forms.CrispyModelForm):

    class Meta:
        model = models.Study
        fields = [
            'shared_with'
        ]

    def clean_shared_with(self):
        shared_with = self.cleaned_data['shared_with']
        if shared_with:
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


class StudyPrivacyForm(contrib_forms.CrispyModelForm):
    optional_label_ignore_fields = [
        'privacy_statement',
    ]

    class Meta:
        model = models.Study
        fields = [
            'privacy_statement',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['privacy_statement'].required = True


class DemographicFieldForm(contrib_forms.CrispyModelForm):

    class Meta:
        model = models.DemographicField
        fields = [
            'name',
        ]


def demographic_formset_factory(n_fields, extra=0):
    return forms.modelformset_factory(
        models.DemographicField,
        form=DemographicFieldForm,
        min_num=n_fields,
        extra=extra,
    )


def demographic_formset_helper():
    formset_helper = FormHelper()
    formset_helper.add_layout(
        Layout(
            Fieldset('Demographic field {{ forloop.counter }}', None, 'name'),
        ),
    )
    formset_helper.add_input(Submit('submit', 'Submit'))
    formset_helper.add_input(Submit('save', 'Save', css_class='btn-secondary'))
    formset_helper.add_input(Submit('add', 'Add', css_class='btn-secondary'))
    formset_helper.add_input(Submit('delete', 'Delete last', css_class='btn-danger'))
    return formset_helper
