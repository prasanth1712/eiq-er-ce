# This Makefile requires the following commands to be available:
# * python3.9
# * docker

# for local development and testing

REQUIREMENTS_PROD:=requirements/prod.txt
REQUIREMENTS_DEV:=requirements/dev.txt

PYTHON_VERSION=python3.9
export SOME_ENV := someTest

.PHONY: pyclean
pyclean:
	@rm -rf *.egg-info build
	@rm -rf coverage.xml .coverage
	@rm -f de-whs-tools-*.tgz

.PHONY: clean
clean: pyclean
	@rm -rf venv

.PHONY: test
test: pyclean lint unittests

.PHONY: unittests
unittests:
	@export ENV=test && \
	export FLASK_APP=manage.py:app && \
	venv/bin/coverage run -m flask test tests/test_manage.py
	@venv/bin/coverage xml -i -o coverage.xml
	
.PHONY: gen_reports
gen_reports:	
	@pycobertura show -f html -o coverage.html coverage.xml
	@junit2html junit.xml test_report.html

# lint/black should run before lint/flake8 because it shows diff for the files to be changed
.PHONY: lint
lint: lint/black lint/flake8 lint/mypy lint/isort

.PHONY: lint/flake8
lint/flake8: 
	@venv/bin/flake8 polylogyx

.PHONY: lint/mypy
lint/mypy:
	@venv/bin/mypy polylogyx

.PHONY: lint/isort
lint/isort: 
	@venv/bin/isort --diff --check polylogyx

.PHONY: lint/black
lint/black: 
	@venv/bin/black --diff --check polylogyx

.PHONY: format
format: format/isort format/black

.PHONY: format/isort
format/isort:
	@venv/bin/isort polylogyx

.PHONY: format/black
format/black:
	@venv/bin/black --verbose polylogyx


################################################
# Setting up of different kinds of virtualenvs #
################################################
#$(VENV_BASE):
base:
	@rm -rf venv
	@$(PYTHON_VERSION) -m venv venv
	
venv_prod: base
	@venv/bin/pip install -r $(REQUIREMENTS_PROD)

venv_dev: venv_prod
	@venv/bin/pip install -r $(REQUIREMENTS_DEV)

###################
# Run application #
###################

run/devserver:
	export ENV=dev && \
	export FLASK_APP=manage.py:app && \
	venv/bin/python flask run

