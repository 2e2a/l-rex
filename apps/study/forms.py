from crispy_forms.helper import FormHelper
from crispy_forms.layout import Fieldset, Layout, Submit
from django import forms
from django.contrib.auth.models import User

from apps.contrib import forms as crispy_forms

from . import models


class StudyForm(crispy_forms.CrispyModelForm):

    class Meta:
        model = models.Study
        fields = [
            'title',
            'item_type',
            'password',
            'require_participant_id',
            'generate_participation_code',
            'end_date',
            'trial_limit'
        ]

    def __init__(self, *args, **kwargs):
        self.disable_itemtype = kwargs.pop('disable_itemtype', False)
        super().__init__(*args, **kwargs)
        if self.disable_itemtype:
            self.fields['item_type'].widget.attrs['readonly'] = True
            self.fields['item_type'].widget.attrs['disabled'] = True


class StudyAdvancedForm(crispy_forms.CrispyModelForm):

    class Meta:
        model = models.Study
        fields = [
            'use_blocks',
            'pseudo_randomize_question_order',
            'enable_item_rating_feedback',
        ]

    def __init__(self, *args, **kwargs):
        self.disable_question_order = kwargs.pop('disable_randomize_question_order', False)
        self.disable_use_blocks = kwargs.pop('disable_use_blocks', False)
        self.disable_feedback = kwargs.pop('disable_feedback', False)
        super().__init__(*args, **kwargs)
        if self.disable_question_order:
            self.fields['pseudo_randomize_question_order'].widget.attrs['readonly'] = True
            self.fields['pseudo_randomize_question_order'].widget.attrs['disabled'] = True
        if self.disable_use_blocks:
            self.fields['use_blocks'].widget.attrs['readonly'] = True
            self.fields['use_blocks'].widget.attrs['disabled'] = True
        if self.disable_feedback:
            self.fields['enable_item_rating_feedback'].widget.attrs['readonly'] = True
            self.fields['enable_item_rating_feedback'].widget.attrs['disabled'] = True


class StudyFromArchiveForm(crispy_forms.CrispyForm):
    file = forms.FileField(
        help_text='An L-Rex archive file previously downloaded.'
    )


class StudyCopyForm(crispy_forms.CrispyForm):
    title = forms.CharField(
        max_length=100,
        help_text='Title of the new study.'
    )


class StudyInstructionsForm(crispy_forms.CrispyModelForm):
    optional_label_ignore_fields = [
        'instructions',
        'outro',
    ]

    class Meta:
        model = models.Study
        fields = [
            'instructions',
            'outro',
            'continue_label',
            'feedback_message',
        ]

    def __init__(self, *args, **kwargs):
        instance = kwargs.get('instance', None)
        if instance and not instance.instructions:
            kwargs['initial'].update({
                'instructions': 'Please rate the following sentences on the scale.',
                'outro': 'Thank you for participating!',
            })
        super().__init__(*args, **kwargs)
        if instance and not instance.enable_item_rating_feedback:
            self.fields['feedback_message'].widget = forms.HiddenInput()


class ArchiveForm(crispy_forms.CrispyModelForm):
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


class QuestionForm(crispy_forms.CrispyModelForm):
    scale_labels = forms.CharField(
        max_length=200,
        required=True,
        help_text='Rating scale labels, separated by commas (e.g. "1,2,3,4,5")'
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

    def clean_scale_labels(self):
        scale_labels = self.cleaned_data['scale_labels']
        if scale_labels and len(scale_labels.split(','))<2:
            raise forms.ValidationError('At least two scale values need to be defined')
        return scale_labels


def question_formset_factory(n_questions, extra=0):
    return forms.modelformset_factory(
        models.Question,
        form=QuestionForm,
        min_num=n_questions,
        extra=extra,
    )


def initialize_with_questions(question_formset, questions):
    for question, form in zip(questions, question_formset):
        form['scale_labels'].initial = ','.join([scale_value.label for scale_value in question.scalevalue_set.all()])


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
    formset_helper.add_input(
        Submit("submit", "Submit"),
    )
    formset_helper.add_input(
        Submit("add", "Add", css_class="btn-secondary"),
    )
    formset_helper.add_input(
        Submit("delete", "Delete last", css_class="btn-danger"),
    )
    return formset_helper


class SharedWithForm(crispy_forms.CrispyModelForm):

    class Meta:
        model = models.Study
        fields = [
            'shared_with'
        ]

    def clean_shared_with(self):
        shared_with = self.cleaned_data['shared_with']
        for username in shared_with.split(','):
            if not User.objects.filter(username=username).exists():
                raise forms.ValidationError('No user with username {} registered'.format(username))
        return shared_with
