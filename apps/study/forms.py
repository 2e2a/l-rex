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
            'use_blocks',
            'pseudo_randomize_question_order',
            'password',
            'require_participant_id',
            'generate_participation_code',
            'end_date',
            'trial_limit'
        ]

    def __init__(self, *args, **kwargs):
        self.disable = kwargs.pop('disable', False)
        self.disable_itemtype = kwargs.pop('disable_itemtype', False)
        super().__init__(*args, **kwargs)
        if self.disable:
            self.fields['title'].widget.attrs['readonly'] = True
            self.fields['use_blocks'].widget.attrs['readonly'] = True
        if self.disable_itemtype:
            self.fields['item_type'].widget.attrs['readonly'] = True

    def clean_title(self):
        if self.disable:
            instance = getattr(self, 'instance', None)
            return instance.title if instance and instance.pk else self.cleaned_data['title']
        else:
            return self.cleaned_data['title']

    def clean_item_type(self):
        if self.disable_itemtype:
            instance = getattr(self, 'instance', None)
            return instance.item_type if instance and instance.pk else self.cleaned_data['item_type']
        else:
            return self.cleaned_data['item_type']

    def clean_use_blocks(self):
        if self.disable:
            instance = getattr(self, 'use_blocks', None)
            return instance.use_blocks if instance and instance.pk else self.cleaned_data['use_blocks']
        else:
            return self.cleaned_data['use_blocks']


class StudyFromArchiveForm(crispy_forms.CrispyForm):
    file = forms.FileField(
        help_text='An L-Rex archive file previously downloaded.'
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
        ]

    def __init__(self, *args, **kwargs):
        instance = kwargs.get('instance', None)
        if instance and not instance.instructions:
            kwargs['initial'].update({
                'instructions': 'Please rate the following sentences on the scale.',
                'outro': 'Thank you for participating!',
            })
        super().__init__(*args, **kwargs)


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
            'legend',
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


def question_formset_helper():
    formset_helper = FormHelper()
    formset_helper.add_layout(
        Layout(
            Fieldset('Question {{ forloop.counter }}', None, 'question', 'scale_labels', 'legend'),
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
