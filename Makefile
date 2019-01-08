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
	wget -N https://raw.githubusercontent.com/FortAwesome/Font-Awesome/master/svgs/solid/info-circle.svg -P lrex/static/icons/
	wget -N https://raw.githubusercontent.com/FortAwesome/Font-Awesome/master/svgs/solid/graduation-cap.svg -P lrex/static/icons/
	wget -N https://raw.githubusercontent.com/FortAwesome/Font-Awesome/master/svgs/solid/book.svg -P lrex/static/icons/
	wget -N https://raw.githubusercontent.com/FortAwesome/Font-Awesome/master/svgs/solid/users.svg -P lrex/static/icons/


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

.PHONY: reset-db
reset-db:
	./scripts/reset_db.sh
	$(VIRTUAL_ENV)/bin/python3 manage.py migrate
	$(VIRTUAL_ENV)/bin/python3 manage.py loaddata fixtures/demo.json

.PHONY: pull
pull:
	git pull

.PHONY: deploy
deploy: pull install build migrate

fixvenv:
	rm -r $(VIRTUAL_ENV)
	python3 -m venv $(VIRTUAL_ENV)
	$(VIRTUAL_ENV)/bin/python3 -m pip install -r requirements.txt
