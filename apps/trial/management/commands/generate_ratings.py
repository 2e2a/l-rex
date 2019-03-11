import random

from django.core.management.base import BaseCommand, CommandError

from apps.study import models as study_models
from apps.trial import models as trial_models


class Command(BaseCommand):
    help = 'Generate random ratings for a study'

    def add_arguments(self, parser):
        parser.add_argument('study_slug', type=str)
        parser.add_argument('n_ratings', type=int)

    def handle(self, *args, **options):
        study_slug = options['study_slug']
        n_ratings = options['n_ratings']
        study = study_models.Study.objects.get(slug=study_slug)
        if not study:
            raise CommandError('Study does not exist.')
        if not study.is_rating_possible:
            raise CommandError('Study does not allow rating.')
        questions_scale_values = []
        for question in study.questions:
            questions_scale_values.append((question.number, question.scalevalue_set.all()))
        for i in range(n_ratings):
            questionnaire = study.next_questionnaire
            trial = trial_models.Trial(
                questionnaire=questionnaire
            )
            if study.require_participant_id:
                trial.subject_id = i
            trial.save()
            for questionnaire_item in questionnaire.questionnaireitem_set.all():
                for question, question_scale_values in questions_scale_values:
                    scale_value = random.choice(question_scale_values)
                    trial_models.Rating.objects.create(
                        trial=trial,
                        questionnaire_item=questionnaire_item,
                        scale_value=scale_value,
                        question=question
                    )
