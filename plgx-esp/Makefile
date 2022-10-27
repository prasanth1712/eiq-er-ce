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

#######################
# DB Schema Migration #
#######################

run/db_upgrade:
	echo "Creating DB schema..."
	flask db upgrade

run/db_roles:
	echo "Creating all basic roles..."
	flask create_all_roles

	echo "Assigning admin role for all the existing users..."
	flask update_role_for_existing_users

	echo "Creating primary admin user..."
	flask add_user $(POLYLOGYX_USER) --password $(POLYLOGYX_PASSWORD) --email $(POLYLOGYX_USER_EMAIL) --role admin --first_name $(POLYLOGYX_USER_FIRST_NAME) --last_name $(POLYLOGYX_USER_LAST_NAME)

run/db_create_partitions:
	echo "Creating buffer partitions..."
	flask add_partition

run/db_load_data_from_backup:
	echo "Creating today's partition from backup..."
	flask create_partition_from_old_data

run/db_load_settings:
	echo "Adding/Updating settings..."
	flask update_settings --data_retention_days $(DATA_RETENTION_DAYS)
	flask set_log_level 
	flask update_vt_av_engines_config --filepath default_data/Virustotal-avengines/default_VT_Av_engines.json
	flask update_vt_match_count --vt_min_match_count $(VT_MIN_MATCH_COUNT)
	flask update_vt_scan_retention_period --vt_scan_retention_period $(VT_SCAN_RETENTION_PERIOD)

	echo "Updating OSQuery Schema from common/osquery_schema.json ..."
	flask update_osquery_schema --file_path common/osquery_schema.json

run/add_threat_intel_keys:
	flask add_api_key --ibm_x_force_key $(IBMxForceKey) --ibm_x_force_pass $(IBMxForcePass)
	flask add_api_key --vt_key $(VT_API_KEY)
	flask add_api_key --otx_key $(ALIENVAULT_OTX_KEY)

run/db_initial_data_load:
	flask remove_unmapped_queries_filters

	echo "Adding default filters..."
	flask add_default_filters --filepath default_data/default_filters/default_filter_linux.conf --platform linux --name Default --is_default true
	flask add_default_filters --filepath default_data/default_filters/default_filter_macos.conf --platform darwin --name Default --is_default true
	flask add_default_filters --filepath default_data/default_filters/default_filter_windows.conf --platform windows --name Default --is_default true
	flask add_default_filters --filepath default_data/default_filters/default_filter_windows_deep.conf --platform windows --name Deep

	echo "Adding default queries..."
	flask add_default_queries --filepath default_data/default_queries/default_queries_linux.conf --platform linux --name Default --is_default true
	flask add_default_queries --filepath default_data/default_queries/default_queries_macos.conf --platform darwin --name Default --is_default true
	flask add_default_queries --filepath default_data/default_queries/default_queries_windows.conf --platform windows --name Default --is_default true
	flask add_default_queries --filepath default_data/default_queries/default_queries_windows_deep.conf --platform windows --name Deep

	echo "updating query name from windows_events to windows_real_time_events for all the configs"
	flask update_wrte_query_name

	echo "Adding default query packs..."
	@ for entry in default_data/packs/* ; do \
	packname="`basename $${entry} .conf`"; \
	flask add_pack --packname $${packname} --filepath $${entry}; \
	done
