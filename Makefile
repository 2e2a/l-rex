VIRTUAL_ENV ?= .env
NODE_MODULES = node_modules
NODE_BIN = $(NODE_MODULES)/.bin

all: help

.PHONY: help
help:
	@echo L-REX development
	@echo TODO

.PHONY: install
install:
	npm install
	if [ ! -f $(VIRTUAL_ENV)/bin/python3 ]; then python3 -m venv $(VIRTUAL_ENV); fi
	$(VIRTUAL_ENV)/bin/python3 -m pip install -r requirements.txt
	wget -N https://raw.githubusercontent.com/FortAwesome/Font-Awesome/master/advanced-options/svg-sprites/fa-solid.svg -P lrex/static/icons/
	$(VIRTUAL_ENV)/bin/python3 manage.py migrate


.PHONY: js
build:
	cp -ra lrex/static/js/ static/
	cp -ra lrex/static/icons/ static/
	cp $(NODE_MODULES)/jquery/dist/jquery.slim.min.js static/js/
	cp $(NODE_MODULES)/popper.js/dist/umd/popper.min.js static/js/
	cp $(NODE_MODULES)/bootstrap/dist/js/bootstrap.min.js static/js/

.PHONY: scss
scss:
	mkdir -p static/css
	$(NODE_BIN)/node-sass lrex/static/scss/style.scss > static/css/lrex.css

.PHONY: build
build: js scss

.PHONY: run
run:
	$(VIRTUAL_ENV)/bin/python3 manage.py runserver 8000

.PHONY: reset
reset:
	psql -U postgres -c 'DROP DATABASE lrex'
	psql -U postgres -c 'CREATE DATABASE lrex OWNER django'
	$(VIRTUAL_ENV)/bin/python3 manage.py migrate
	#$(VIRTUAL_ENV)/bin/python3 manage.py loaddata fixtures/init.json
