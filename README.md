# L-REX

Platform for linguistic rating experiments.

## Requirements

- [python](https://www.python.org/)

- [Django](https://www.djangoproject.com/)

- [django-crispy-forms](https://github.com/django-crispy-forms/django-crispy-forms)

- [pytz](https://pythonhosted.org/pytz/) (Django dependency)

- [psycopg2](http://initd.org/psycopg/) (When using PostgreSQL)

- [bootstrap](https://getbootstrap.com/)

- [jquery](https://jquery.com/)

- [popper.js](https://popper.js.org/)

- [Font Awesome](https://fontawesome.com/)

- [node-sass](https://github.com/sass/node-sass)


## Installation

```
    make install
    make build
```

## Configuration

Configuration parameters (e.g. `DATABASES`)can be overwritten in `lrex/local.conf`.

## Usage

```
    ./manage.py migrate
    ./manage.py createsuperuser
    make run
```

Use Django Admin to create further users under /admin/.
