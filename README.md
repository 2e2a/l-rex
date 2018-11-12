# L-REX

Platform for linguistic rating experiments.

## Requirements

- [python](https://www.python.org/)
- [Django](https://www.djangoproject.com/)
- [django-crispy-forms](https://github.com/django-crispy-forms/django-crispy-forms)
- [django-allauth](https://github.com/pennersr/django-allauth)
- [psycopg2](http://initd.org/psycopg/) (When using PostgreSQL)
- [python-memcached ](https://github.com/linsomniac/python-memcached) (When using caching)
- [bootstrap](https://getbootstrap.com/)
- [jquery](https://jquery.com/)
- [popper.js](https://popper.js.org/)
- [Font Awesome](https://fontawesome.com/)
- [node-sass](https://github.com/sass/node-sass)


## Installation

```
make deploy
```

## Configuration

Configuration parameters (e.g. `DATABASES`) can be overwritten in `lrex/local.conf`.
Add a `Site` for your domain (used by allauth).

## Usage

```
make run
```
