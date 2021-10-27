VIRTUAL_ENV ?= .venv
NODE_MODULES = node_modules
NODE_BIN = $(NODE_MODULES)/.bin

all: help

.PHONY: help
help:
	@echo L-REX development helper

.PHONY: python
python:
	if [ ! -f $(VIRTUAL_ENV)/bin/python3 ]; then python3 -m venv $(VIRTUAL_ENV); fi
	$(VIRTUAL_ENV)/bin/python3 -m pip install -r requirements.txt


.PHONY: node
node:
	npm install

.PHONY: install
install: python node

.PHONY: update
update:
	npm update
	$(VIRTUAL_ENV)/bin/pip-compile -U requirements.in


.PHONY: js
js:
	mkdir -p lrex/static/js
	cp $(NODE_MODULES)/jquery/dist/jquery.slim.min.js lrex/static/js/
	cp $(NODE_MODULES)/bootstrap/dist/js/bootstrap.bundle.min.js lrex/static/js/

.PHONY: scss
scss:
	mkdir -p lrex/static/css
	$(NODE_BIN)/node-sass lrex/assets/scss/style.scss > lrex/static/css/lrex.css

.PHONY: build
build: js scss

.PHONY: migrate
migrate:
	$(VIRTUAL_ENV)/bin/python3 manage.py migrate

.PHONY: makemigrations
makemigrations:
	$(VIRTUAL_ENV)/bin/python3 manage.py makemigrations

.PHONY: run
run:
	$(VIRTUAL_ENV)/bin/python3 manage.py runserver 8000

.PHONY: backup
backup:
	$(VIRTUAL_ENV)/bin/python3 manage.py dumpdata auth.user account lrex_home lrex_study lrex_materials lrex_item lrex_trial --indent 4 > fixtures/backup.json

.PHONY: restore
restore:
	$(VIRTUAL_ENV)/bin/python3 manage.py loaddata fixtures/backup.json


.PHONY: demo-save
demo-save:
	$(VIRTUAL_ENV)/bin/python3 manage.py dumpdata lrex_study lrex_materials lrex_item lrex_trial --indent 4 > fixtures/demo.json

.PHONY: demo-load
demo-load:
	$(VIRTUAL_ENV)/bin/python3 manage.py migrate
	$(VIRTUAL_ENV)/bin/python3 manage.py loaddata fixtures/users.json
	$(VIRTUAL_ENV)/bin/python3 manage.py loaddata fixtures/demo.json

.PHONY: db-reset
db-reset:
	./scripts/reset_db.sh

.PHONY: dev-reset
dev-reset: db-reset demo-load

.PHONY: clean
clean:
	find . -type f -name '*.py[co]' -delete -o -type d -name __pycache__ -delete

.PHONY: pull
pull:
	git pull

.PHONY:  static
static:
	$(VIRTUAL_ENV)/bin/python3 manage.py collectstatic --noinput

.PHONY: deploy
deploy: clean pull install build migrate static

.PHONY: fixenv
fixvenv:
	rm -r $(VIRTUAL_ENV)
	python3 -m venv $(VIRTUAL_ENV)
	$(VIRTUAL_ENV)/bin/python3 -m pip install -r requirements.txt
