VIRTUAL_ENV ?= .env
NODE_MODULES = node_modules
NODE_BIN = $(NODE_MODULES)/.bin

all: help

.PHONY: help
help:
	@echo mein.berlin development tools
	@echo
	@echo It will either use an exisiting virtualenv if it was entered
	@echo before or create a new one in the .env subdirectory.
	@echo
	@echo usage:
	@echo
	@echo "  make install         -- install dev setup"
	@echo "  make build           -- build js and css and create new po and mo files"
	@echo "  make run             -- start a dev server"
	@echo

.PHONY: install
install:
	npm install
	if [ ! -f $(VIRTUAL_ENV)/bin/python3 ]; then python3 -m venv $(VIRTUAL_ENV); fi
	$(VIRTUAL_ENV)/bin/python3 -m pip install -r requirements.txt
	$(VIRTUAL_ENV)/bin/python3 manage.py migrate


.PHONY: js
build:
	cp lrex/static/js/* static/js/
	cp $(NODE_MODULES)/jquery/dist/jquery.slim.min.js static/js/
	cp $(NODE_MODULES)/bootstrap/dist/js/bootstrap.min.js static/js/

.PHONY: scss
scss:
	mkdir -p static/css
	$(NODE_BIN)/node-sass lrex/static/scss/style.scss > static/css/lrex.css

.PHONY: build
build: js scss

.PHONY: run
server:
	$(VIRTUAL_ENV)/bin/python3 manage.py runserver 8000
