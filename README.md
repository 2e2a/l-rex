# L-Rex

L-Rex is a platform for linguistic rating experiments. It is designed for experiments in which participants are asked to rate stimuli (e.g., sentences) on an n-point scale (e.g., a scale from 1-5).

Read the [Wiki](https://github.com/2e2a/l-rex/wiki) for more information.

## Try it out

We are currently running a free instance of L-Rex on our private server at [https://lrex.2e2a.de](https://lrex.2e2a.de). Feel free to use it for your studies.

## Deploy it on your own server

### Requirements

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


### Installation

```
make deploy
```

### Configuration

Configuration parameters (e.g. `DATABASES`) can be overwritten in `lrex/local.conf`.
Add a `Site` for your domain (used by allauth).

### Usage

```
make run
```
