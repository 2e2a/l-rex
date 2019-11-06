VIRTUAL_ENV ?= .venv
NODE_MODULES = node_modules
NODE_BIN = $(NODE_MODULES)/.bin

all: help

.PHONY: help
help:
	@echo L-REX development
	@echo TODO

.PHONY: python
python:
	if [ ! -f $(VIRTUAL_ENV)/bin/python3 ]; then python3 -m venv $(VIRTUAL_ENV); fi
	$(VIRTUAL_ENV)/bin/python3 -m pip install -r requirements.txt

.PHONY: node
node:
	npm install

.PHONY: icons
icons:
	wget -nv -N https://raw.githubusercontent.com/FortAwesome/Font-Awesome/master/svgs/solid/bullhorn.svg -P lrex/static/icons/
	wget -nv -N https://raw.githubusercontent.com/FortAwesome/Font-Awesome/master/svgs/solid/clipboard-list.svg -P lrex/static/icons/
	wget -nv -N https://raw.githubusercontent.com/FortAwesome/Font-Awesome/master/svgs/solid/clock.svg -P lrex/static/icons/
	wget -nv -N https://raw.githubusercontent.com/FortAwesome/Font-Awesome/master/svgs/solid/cog.svg -P lrex/static/icons/
	wget -nv -N https://raw.githubusercontent.com/FortAwesome/Font-Awesome/master/svgs/solid/envelope.svg -P lrex/static/icons/
	wget -nv -N https://raw.githubusercontent.com/FortAwesome/Font-Awesome/master/svgs/solid/file-upload.svg -P lrex/static/icons/
	wget -nv -N https://raw.githubusercontent.com/FortAwesome/Font-Awesome/master/svgs/solid/info-circle.svg -P lrex/static/icons/
	wget -nv -N https://raw.githubusercontent.com/FortAwesome/Font-Awesome/master/svgs/solid/lightbulb.svg -P lrex/static/icons/
	wget -nv -N https://raw.githubusercontent.com/FortAwesome/Font-Awesome/master/svgs/solid/list-ul.svg -P lrex/static/icons/
	wget -nv -N https://raw.githubusercontent.com/FortAwesome/Font-Awesome/master/svgs/solid/list-ol.svg -P lrex/static/icons/
	wget -nv -N https://raw.githubusercontent.com/FortAwesome/Font-Awesome/master/svgs/solid/poll.svg -P lrex/static/icons/
	wget -nv -N https://raw.githubusercontent.com/FortAwesome/Font-Awesome/master/svgs/solid/question-circle.svg -P lrex/static/icons/

.PHONY: install
install: python node icons

.PHONY: update
update:
	npm update
	$(VIRTUAL_ENV)/bin/python3 -m pip install --upgrade --upgrade-strategy eager -r requirements-dev.txt
	$(VIRTUAL_ENV)/bin/python3 -m pip freeze > requirements.txt


.PHONY: js
js:
	mkdir -p lrex/static/js
	cp $(NODE_MODULES)/jquery/dist/jquery.slim.min.js lrex/static/js/
	cp $(NODE_MODULES)/popper.js/dist/umd/popper.min.js lrex/static/js/
	cp $(NODE_MODULES)/bootstrap/dist/js/bootstrap.min.js lrex/static/js/

.PHONY: scss
scss:
	mkdir -p lrex/static/css
	$(NODE_BIN)/node-sass lrex/assets/scss/style.scss > lrex/static/css/lrex.css

.PHONY: build
build: js scss

.PHONY: migrate
migrate:
	$(VIRTUAL_ENV)/bin/python3 manage.py migrate

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
	$(VIRTUAL_ENV)/bin/python3 manage.py dumpdata --natural-foreign --exclude auth.permission --exclude contenttypes --indent 4 > fixtures/demo.json

.PHONY: demo-load
demo-load:
	$(VIRTUAL_ENV)/bin/python3 manage.py migrate
	$(VIRTUAL_ENV)/bin/python3 manage.py loaddata fixtures/demo.json

.PHONY: reset-db
reset-db:
	./scripts/reset_db.sh

.PHONY: reset-dev
reset-dev: reset-db demo-load

.PHONY: pull
pull:
	git pull

.PHONY:  static
static:
	$(VIRTUAL_ENV)/bin/python3 manage.py collectstatic --noinput

.PHONY: deploy
deploy: pull install build migrate static

.PHONY: fixenv
fixvenv:
	rm -r $(VIRTUAL_ENV)
	python3 -m venv $(VIRTUAL_ENV)
	$(VIRTUAL_ENV)/bin/python3 -m pip install -r requirements.txt
