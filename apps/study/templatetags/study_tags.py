from django import template

from apps.study import models


register = template.Library()


@register.filter
def is_progress_std_created(study):
    return study.progress == models.Study.PROGRESS_STD_CREATED

@register.filter
def is_progress_std_created_reached(study):
    return study.progress_reached(models.Study.PROGRESS_STD_CREATED)


@register.filter
def is_progress_std_scale_configured(study):
    return study.progress == models.Study.PROGRESS_STD_SCALE_CONFIGURED


@register.filter
def is_progress_std_scale_configured_reached(study):
    return study.progress_reached(models.Study.PROGRESS_STD_SCALE_CONFIGURED)


@register.filter
def is_progress_exp_created(study):
    return study.progress == models.Study.PROGRESS_EXP_CREATED


@register.filter
def is_progress_exp_created_reached(study):
    return study.progress_reached(models.Study.PROGRESS_EXP_CREATED)


@register.filter
def is_progress_exp_items_created(study):
    return study.progress == models.Study.PROGRESS_EXP_ITEMS_CREATED


@register.filter
def is_progress_exp_items_created_reached(study):
    return study.progress_reached(models.Study.PROGRESS_EXP_ITEMS_CREATED)


@register.filter
def is_progress_exp_items_validated(study):
    return study.progress == models.Study.PROGRESS_EXP_ITEMS_VALIDATED


@register.filter
def is_progress_exp_items_validated_reached(study):
    return study.progress_reached(models.Study.PROGRESS_EXP_ITEMS_VALIDATED)


@register.filter
def is_progress_exp_lists_created(study):
    return study.progress == models.Study.PROGRESS_EXP_LISTS_CREATED


@register.filter
def is_progress_exp_lists_created_reached(study):
    return study.progress_reached(models.Study.PROGRESS_EXP_LISTS_CREATED)


@register.filter
def is_progress_std_questionnares_generated(study):
    return study.progress == models.Study.PROGRESS_STD_QUESTIONNARES_GENERATED


@register.filter
def is_progress_std_questionnares_generated_reached(study):
    return study.progress_reached(models.Study.PROGRESS_STD_QUESTIONNARES_GENERATED)


@register.filter
def is_progress_std_run(study):
    return study.progress == models.Study.PROGRESS_STD_RUN


@register.filter
def is_progress_std_run_reached(study):
    return study.progress_reached(models.Study.PROGRESS_STD_RUN)
