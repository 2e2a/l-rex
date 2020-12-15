from django.utils.text import slugify


def slugify_unique(value, model, self_id=None):
    slug = slugify(value)
    unique_slug = slug
    i = 1
    while model.objects.filter(slug=unique_slug).exclude(id=self_id).count() > 0:
        unique_slug = '{}-{}'.format(slug, i)
        i += 1
    return unique_slug


def split_list_string(value):
    values = []
    if not value:
        return values
    end = 0
    while True:
        end = value.find(',', end + 1)
        if end > 0:
            is_escaped = value[end - 1] == '\\' if end > 1 else False
            if not is_escaped:
                values.append(value[:end].replace('\\',''))
                value = value[end + 1:]
                end = 0
        else:
            values.append(value.strip().replace('\\',''))
            break
    return values


def to_list_string(value_list):
    return ','.join(str(value).replace(',', '\\,') for value in value_list)
