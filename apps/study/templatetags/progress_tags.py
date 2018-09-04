from django import template

from apps.experiment.models import Experiment
from apps.study.models import Study


register = template.Library()


@register.filter
def is_progress_std_created(study):
    return study.progress == Study.PROGRESS_STD_CREATED

@register.filter
def is_progress_std_created_reached(study):
    return study.progress_reached(Study.PROGRESS_STD_CREATED)


@register.filter
def is_progress_std_question_created(study):
    return study.progress == Study.PROGRESS_STD_QUESTION_CREATED


@register.filter
def is_progress_std_question_created_reached(study):
    return study.progress_reached(Study.PROGRESS_STD_QUESTION_CREATED)


@register.filter
def is_progress_std_question_completed(study):
    return study.progress == Study.PROGRESS_STD_QUESTION_COMPLETED


@register.filter
def is_progress_std_question_completed_reached(study):
    return study.progress_reached(Study.PROGRESS_STD_QUESTION_COMPLETED)


@register.filter
def is_progress_std_exp_created(study):
    return study.progress == Study.PROGRESS_STD_EXP_CREATED


@register.filter
def is_progress_std_exp_created_reached(study):
    return study.progress_reached(Study.PROGRESS_STD_EXP_CREATED)


@register.filter
def is_progress_exp_items_created(experiment):
    return experiment.progress == Experiment.PROGRESS_EXP_ITEMS_CREATED


@register.filter
def is_progress_exp_items_created_reached(experiment):
    return experiment.progress_reached(Experiment.PROGRESS_EXP_ITEMS_CREATED)


@register.filter
def is_progress_exp_items_validated(experiment):
    return experiment.progress == Experiment.PROGRESS_EXP_ITEMS_VALIDATED


@register.filter
def is_progress_exp_items_validated_reached(experiment):
    return experiment.progress_reached(Experiment.PROGRESS_EXP_ITEMS_VALIDATED)


@register.filter
def is_progress_exp_lists_created(experiment):
    return experiment.progress == Experiment.PROGRESS_EXP_LISTS_CREATED


@register.filter
def is_progress_exp_lists_created_reached(experiment):
    experiment.progress_reached(Experiment.PROGRESS_EXP_LISTS_CREATED)


@register.filter
def is_progress_std_exp_completed(study):
    return study.progress == Study.PROGRESS_STD_EXP_COMPLETED


@register.filter
def is_progress_std_exp_completed_reached(study):
    return study.progress_reached(Study.PROGRESS_STD_EXP_COMPLETED)


@register.filter
def is_progress_std_questionnares_generated(study):
    return study.progress == Study.PROGRESS_STD_QUESTIONNARES_GENERATED


@register.filter
def is_progress_std_questionnares_generated_reached(study):
    return study.progress_reached(Study.PROGRESS_STD_QUESTIONNARES_GENERATED)


@register.filter
def is_progress_std_published(study):
    return study.progress == Study.PROGRESS_STD_PUBLISHED


@register.filter
def is_progress_std_published_reached(study):
    return study.progress_reached(Study.PROGRESS_STD_PUBLISHED)
