# L-Rex

L-Rex is a platform for linguistic rating experiments. It is designed for experiments in which participants are asked to rate stimuli (e.g., sentences) on an n-point scale (e.g., a scale from 1-5).

Read the [Wiki](https://github.com/2e2a/l-rex/wiki) for more information.

## Try it out on our server

We are currently running an instance of L-Rex at [https://www.l-rex.de](https://www.l-rex.de). Feel free to use it for your studies.

## Try it out locally

To try out L-Rex locally:

```
make install-dev
make run
```

This installs L-Rex including development tools and imports demo studies and test users.
You can log in as "user" or "admin" with the password "lrexlrex".

Configuration parameters (e.g. `DATABASES`) can be overwritten in `lrex/local.py`.

## Dependencies

- [python](https://www.python.org/)
- [Django](https://www.djangoproject.com/)
- [django-crispy-forms](https://github.com/django-crispy-forms/django-crispy-forms)
- [django-registration](https://github.com/ubernostrum/django-registration)
- [psycopg2](http://initd.org/psycopg/) (When using PostgreSQL)
- [bootstrap](https://getbootstrap.com/)
- [jquery](https://jquery.com/)
- [popper.js](https://popper.js.org/)
- [node-sass](https://github.com/sass/node-sass)
