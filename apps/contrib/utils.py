from django.utils.text import slugify


def slugify_unique(value, model, self_id=None):
    slug=slugify(value)
    unique_slug = slug
    i = 1
    while model.objects.filter(slug=unique_slug).exclude(id=self_id).count() > 0:
        unique_slug = '{}-{}'.format(slug, i)
        i += 1
    return unique_slug
