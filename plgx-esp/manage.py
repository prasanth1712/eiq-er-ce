#!/usr/bin/env python
# set async_mode to 'threading', 'eventlet', 'gevent' or 'gevent_uwsgi' to
# force a mode else, the best mode is selected automatically from what's
# installed
# -*- coding: utf-8 -*-
import datetime as dt
import glob
from io import BytesIO
import gzip
import psutil
import os
from os.path import abspath, dirname, join
import click

from flask import json, current_app, jsonify, request
from sqlalchemy import or_
from werkzeug.middleware.proxy_fix import ProxyFix

from polylogyx import create_app, db
from polylogyx.celery.tasks import create_daily_partition, create_index_for_result_log
from polylogyx.constants import (DefaultInfoQueries, SettingsVariables)
from polylogyx.db.models import Query, Rule, Settings, DefaultFilters, DefaultQuery, Config, \
    VirusTotalAvEngines, Role, User, ThreatIntelCredentials
from polylogyx.extensions import bcrypt
from polylogyx.settings import CurrentConfig, DevConfig, TestConfig
from distutils.util import strtobool


app = create_app(config=CurrentConfig)
app.wsgi_app = ProxyFix(app.wsgi_app)

override_default_data = strtobool(str(os.environ.get('OVERRIDE_DEFAULT_DATA', 'True')))


@click.argument('remaining', required=False)
@app.cli.command("test", help="Runs unit testcases")
def test(remaining=[]):
    test_cls = Test()
    if remaining:
        remaining = [remaining]
    test_cls.run(remaining)


@app.before_request
def before_request_method():
    from polylogyx.utils.cache import get_average_celery_task_wait_time, get_a_setting
    from polylogyx.utils.log_setting import set_app_log_level
    # Gzip processing
    if 'Content-Encoding' in request.headers and \
            request.headers['Content-Encoding'] == 'gzip':
        request._cached_data = gzip.GzipFile(
            fileobj=BytesIO(request.get_data())).read()

    drop_request = False
    request_json = request.get_json()
    pool = db.engine.pool
    try:
        log_level = "WARNING"
        log_level_setting = get_a_setting('er_log_level')
        if log_level_setting:
            log_level = log_level_setting
        set_app_log_level(log_level)
        if request.url_rule.endpoint == 'api.logger' and request_json['log_type'] == 'result':
            if os.environ.get('MAX_CPU_LIMIT') and psutil.cpu_percent() > int(os.environ.get('MAX_CPU_LIMIT')):
                current_app.logger.critical("CPU usage({}%) reached bottle neck, So dropping the result log payload!"
                                            .format(psutil.cpu_percent()))
                drop_request = True
            elif os.environ.get('MAX_RAM_LIMIT') and psutil.virtual_memory()[2] > int(os.environ.get('MAX_RAM_LIMIT')):
                current_app.logger.critical("RAM usage({}%) reached bottle neck, So dropping the result log payload!"
                                            .format(psutil.virtual_memory()[2]))
                drop_request = True
            elif os.environ.get('MIN_POSTGRES_CONN_REQUIRED') and \
                    pool.size()-pool.checkedout() < int(os.environ.get('MIN_POSTGRES_CONN_REQUIRED')):
                current_app.logger.critical("""POSTGRES active connections({} available) outage, 
                So dropping the result log payload!""".format(pool.size()-pool.checkedout()))
                drop_request = True
            elif os.environ.get('MAX_EVENTS_COUNT'):
                events_count = 0
                for entry in request_json['data']:
                    if 'snapshot' in entry:
                        events_count += len(entry['snapshot'])
                    else:
                        events_count += 1
                if events_count > int(os.environ.get('MAX_EVENTS_COUNT')):
                    current_app.logger.info("""Events count received({}) is more, So dropping the result log payload!"""
                                            .format(events_count))
                    drop_request = True
            elif os.environ.get('MAX_CELERY_TASK_WAIT_TIME'):
                avg_task_wait_time = get_average_celery_task_wait_time()
                if avg_task_wait_time and avg_task_wait_time > int(os.environ.get('MAX_CELERY_TASK_WAIT_TIME')):
                    current_app.logger.critical(
                        """Celery task wait time({} sec) is high due to load, So dropping the result log payload!"""
                        .format(avg_task_wait_time))
                    drop_request = True

        if drop_request:
            current_app.logger.info("Could not process the request due to resources outage or payload size!")
            return jsonify(node_invalid=False,
                           message='Could not process the request due to resources outage or payload size!',
                           status='failure')
    except Exception as e:
        current_app.logger.error(str(e))


class Test:
    name = "test"
    capture_all_args = True

    def run(self, remaining):
        import pytest

        test_path = join(abspath(dirname(__file__)), "tests")

        if remaining:
            test_args = remaining + ["--verbose", "--junitxml=./junit.xml"]
        else:
            test_args = [test_path, "--verbose", "--junitxml=./junit.xml"]

        exit_code = pytest.main(test_args)
        return exit_code


def add_default_filters(filepath, platform, name, is_default):
    from polylogyx.utils.cache import refresh_cached_config
    current_app.logger.info("Adding default filters for config with name '{0}' and with platform '{1}'...".format(name, platform))
    if is_default:
        description = (
            "Lightweight configuration for {0} hosts, also used as default".format(
                platform
            )
        )
    else:
        description = "A Sample configuration with additional queries and filters enabled for advanced forensics and monitoring"
    config = (
        db.session.query(Config)
        .filter(Config.name == name)
        .filter(Config.platform == platform)
        .first()
    )
    if not config:
        config = Config.create(
            platform=platform, name=name, is_default=is_default, description=description
        )
        config.save()
        current_app.logger.info(
            "Created a new config '{0}' and adding the filters provided...".format(config))
    else:
        current_app.logger.info(
            "Updating the existing config '{0}'...".format(config))
    existing_filter = DefaultFilters.query.filter_by(config_id=config.id).first()
    try:
        json_str = open(filepath, 'r').read()
        filter = json.loads(json_str)
        if existing_filter and override_default_data:
            current_app.logger.info("Filter already exists, Updating...")
            config.update(is_default=is_default, description=description)
            existing_filter.filters = filter
            existing_filter.update(existing_filter)
        elif existing_filter:
            current_app.logger.info("Filter already exists, Skipping...")
        else:
            current_app.logger.info("Filter does not exist, Creating...")
            DefaultFilters.create(filters=filter, created_at=dt.datetime.utcnow(),
                                  config_id=config.id)
        config.update(updated_at=dt.datetime.utcnow())
        refresh_cached_config()
    except Exception as error:
        current_app.logger.error(str(error))


@click.option("--filepath", help='Path of the json file', type=str)
@click.option("--platform", help='Platform of config', type=str)
@click.option("--name", help='Name of config', type=str)
@click.option("--is_default", default=False, type=bool,
              help='True if the config is the default/primary config of the platform')
@app.cli.command("add_default_filters", help="Adds/updates filters to the default configs of the platform")
def add_default_filters_command(filepath, platform, name, is_default):
    add_default_filters(filepath, platform, name, is_default)


def delete_existing_unmapped_queries_filters():
    current_app.logger.info("Deleting the existing unmapped Queries and Filters...")
    db.session.query(DefaultQuery).filter(DefaultQuery.config_id == None).delete()
    db.session.query(DefaultFilters).filter(DefaultFilters.config_id == None).delete()
    db.session.commit()


@app.cli.command("remove_unmapped_queries_filters",
                 help="Removes all the default queries that aren't mapped to any config")
def delete_existing_unmapped_queries_filters_command():
    delete_existing_unmapped_queries_filters()


def add_default_queries(filepath, platform, name, is_default):
    from polylogyx.utils.cache import refresh_cached_config

    try:
        if is_default:
            description = "Default configuration of {0} hosts".format(platform)
        else:
            description = "A Sample configuration with suggested queries and filters to monitor host state"
        current_app.logger.info("Adding default queries for config with name '{0}' and with platform '{1}'..."
                                .format(name, platform))
        json_str = open(filepath, 'r').read()
        query = json.loads(json_str)
        queries = query['schedule']
        config = db.session.query(Config).filter(Config.name == name).filter(Config.platform == platform).first()
        if config:
            DefaultQuery.query.filter(DefaultQuery.config_id == config.id).filter(
                ~DefaultQuery.name.in_(queries.keys())
            ).delete(synchronize_session=False)
            if override_default_data:
                config.update(is_default=is_default, description=description)
        else:
            config = Config.create(platform=platform, name=name, is_default=is_default, description=description)
        for query_key in queries.keys():
            if query_key not in DefaultInfoQueries.DEFAULT_VERSION_INFO_QUERIES.keys():
                query_filter = DefaultQuery.query.filter_by(name=query_key)\
                    .filter_by(config_id=config.id)
                config_id = config.id
            else:
                query_filter = DefaultQuery.query.filter_by(name=query_key)
                config_id = None
            query = query_filter.first()
            try:
                if "snapshot" in queries[query_key]:
                    snapshot = queries[query_key]["snapshot"]
                else:
                    snapshot = False

                if query and override_default_data:
                    current_app.logger.info(f"Default query with name '{query_key}' already exists, Updating...")
                    query.sql = queries[query_key]["query"]
                    query.interval = queries[query_key]["interval"]
                    query.status = queries[query_key].get("status", True)
                    query.snapshot = snapshot
                    query.update(query)
                elif query:
                    current_app.logger.info(f"Default query with name '{query_key}' already exists, Skipping...")
                else:
                    current_app.logger.info(f"Default query with name '{query_key}' doesn't exists, Creating...")
                    status = queries[query_key].get("status", True)

                    DefaultQuery.create(
                        name=query_key,
                        sql=queries[query_key]["query"],
                        config_id=config_id,
                        interval=queries[query_key]["interval"],
                        status=status,
                        description=queries[query_key].get("description"),
                        snapshot=snapshot,
                    )
            except Exception as error:
                current_app.logger.error(str(error))
        config.update(updated_at=dt.datetime.utcnow())
        refresh_cached_config()
    except Exception as error:
        current_app.logger.error(str(error))


@click.option("--filepath", help='Path of the json file', type=str)
@click.option("--platform", help='Platform of config')
@click.option("--name", help='Name of config')
@click.option("--is_default", default=False, type=bool,
              help='True if the config is the default/primary config of the platform')
@app.cli.command("add_default_queries", help="Adds/updates queries to the default configs of the platform")
def add_default_queries_command(filepath, platform, name, is_default):
    add_default_queries(filepath, platform, name, is_default)


def update_query_name_for_custom_config():
    configs = db.session.query(Config).filter(Config.platform == 'windows').all()
    for config in configs:
        default_query = DefaultQuery.query.filter(DefaultQuery.config_id == config.id).\
            filter(DefaultQuery.name == 'windows_events').first()
        if default_query:
            default_query.update(name='windows_real_time_events')
    db.session.commit()


@app.cli.command("update_wrte_query_name",
                 help="Renames the query windows_events to windows_real_time_events if present")
def update_query_name_for_custom_config_command():
    update_query_name_for_custom_config()


def add_pack(packname, filepath):
    from polylogyx.db.models import Pack

    existing_pack = Pack.query.filter_by(name=packname).first()
    try:
        json_str = open(filepath, 'r').read()
        data = json.loads(json_str)
        if existing_pack and override_default_data:
            pack = existing_pack
            current_app.logger.info(f"Pack with name '{packname}' already exists, Updating...")
        elif existing_pack:
            current_app.logger.info(f"Pack with name '{packname}' already exists, Skipping...")
            exit(0)
        else:
            current_app.logger.info(f"Pack with name '{packname}' doesn't exists, Creating...")
            pack = Pack.create(name=packname)
        for query_name, query in data['queries'].items():
            is_query_exist=False
            queries = Query.query.filter(Query.name == query_name).all()
            if not queries:
                q = Query.create(name=query_name, **query)
                pack.queries.append(q)
                is_query_exist = True
                current_app.logger.info(f"Adding new query {q.name} to pack {pack.name}")
            for q in queries:
                if q.sql == query['query']:
                    is_query_exist=True
                    current_app.logger.info(f"Adding existing query {q.name} to pack {pack.name}")
                    pack.queries.append(q)
                else:
                    pass

            if is_query_exist is False:
                q2 = Query.create(name=query_name, **query)
                current_app.logger.info("Created another query named {0}, but different sql: {1} vs {2}"
                                        .format(query_name, q2.sql.encode('utf-8'), q.sql.encode('utf-8')))
                pack.queries.append(q2)
        pack.save()
    except Exception as error:
        current_app.logger.error("Failed to create pack {0} - {1}".format(packname, error))
        exit(1)


@click.option("--packname", help="Name of the pack")
@click.option("--filepath", help="Path of the query pack json file")
@app.cli.command("add_pack", help="Adds a query pack into the database")
def add_pack_command(packname, filepath):
    add_pack(packname, filepath)


def add_partition():
    for i in range(SettingsVariables.pre_create_partitions_count):
        create_daily_partition(day_delay=i)


@app.cli.command("add_partition", help="Adds a new partition to ResultLog table")
def add_partition_command():
    add_partition()


def add_rules(filepath):
    from polylogyx.utils.cache import refresh_cached_rules
    with open(filepath) as f:
        rules = json.load(f)

    for name, data in rules.items():
        rule = Rule.query.filter_by(name=data["name"]).first()
        if rule and override_default_data:
            current_app.logger.info(f"Rule with name '{rule.name}' already exists, Updating...")
            rule.platform = data.get('platform')
            rule.description = data.get('description')
            rule.conditions = data.get('conditions')
            rule.status = data.get('status', Rule.ACTIVE)
            rule.alert_description = data.get('alert_description', False)
            rule.tactics = data.get("tactics")
            rule.technique_id = data.get("technique_id")
            rule.type = data.get("type", Rule.MITRE)
            rule.save(rule)
        elif rule:
            current_app.logger.info(f"Rule with name '{rule.name}' already exists, Skipping...")
        else:
            current_app.logger.info(f"Rule with name '{data['name']}' doesn't exists, Creating...")
            severity = str(data.get('severity', 'MEDIUM')).upper()
            if severity == 'WARNING':
                severity = Rule.MEDIUM
            rule = Rule(name=data['name'],
                        platform=data.get('platform', 'windows'),
                        alert_description=data.get('alert_description', False),
                        alerters=data.get('alerters'),
                        description=data.get('description'),
                        conditions=data.get('conditions'),
                        status=data.get('status', Rule.ACTIVE),
                        technique_id=data.get('technique_id'),
                        tactics=data.get('tactics'),
                        severity=severity,
                        type=data.get('type', Rule.MITRE))
            rule.save()
    refresh_cached_rules()


@click.option('--filepath', help="Path of the rule json file")
@app.cli.command("add_rule", help="Adds a rule")
def add_rules_command(filepath):
    add_rules(filepath)


def add_default_vt_av_engines(filepath):
    try:
        current_app.logger.info('Adding/Updating Virus total AntiVirus engines config...')
        json_str = open(filepath, 'r').read()
        av_engine = json.loads(json_str)

        av_engines = av_engine['av_engines']
        for key in av_engines.keys():
            av_engine_obj = VirusTotalAvEngines.query.filter(VirusTotalAvEngines.name == key).first()
            if av_engine_obj and override_default_data:
                av_engine_obj.status = av_engines[key]["status"]
                av_engine_obj.save()
            elif av_engine_obj:
                pass
            else:
                VirusTotalAvEngines.create(name=key, status=av_engines[key]["status"])
    except Exception as error:
        current_app.logger.error("Error updating default VirusTotal AV Engines info - {0}".format(str(error)))
    db.session.commit()


@click.option('--filepath', help="Path of the file")
@app.cli.command("update_vt_av_engines_config",
                 help="Updates the Virus Total AV engines config that's being used in the platform")
def add_default_vt_av_engines_command(filepath):
    add_default_vt_av_engines(filepath)


def update_vt_match_count(vt_min_match_count):
    from polylogyx.utils.cache import add_or_update_cached_setting
    existing_setting_obj = Settings.query.filter(Settings.name == 'virustotal_min_match_count').first()
    if existing_setting_obj and override_default_data:
        current_app.logger.info(f"Virus Total minimum match count setting already exists and is set to {existing_setting_obj.setting}, Updating to {vt_min_match_count}...")
        existing_setting_obj.setting = vt_min_match_count
        existing_setting_obj.save()
    elif existing_setting_obj:
        current_app.logger.info(f"Virus Total minimum match count setting already exists and is set to {existing_setting_obj.setting}, Skipping...")
    else:
        settings_obj = Settings.create(name='virustotal_min_match_count', setting=vt_min_match_count)
        current_app.logger.info(f"Virus Total minimum match count setting doesn't exists, Creating it to {vt_min_match_count}...")
        add_or_update_cached_setting(setting_obj=settings_obj)


@click.option("--vt_min_match_count", help="Virus total minimum av engines match count")
@app.cli.command("update_vt_match_count",
                 help="Updates the Virus Total AV engines minimum match count value that's being used in the platform")
def update_vt_match_count_command(vt_min_match_count):
    update_vt_match_count(vt_min_match_count)


def update_vt_scan_retention_period(vt_scan_retention_period):
    from polylogyx.utils.cache import add_or_update_cached_setting
    existing_setting_obj = Settings.query.filter(Settings.name == 'vt_scan_retention_period').first()
    if existing_setting_obj and override_default_data:
        current_app.logger.info(f"Virus Total scan retention period already exists and is set to {existing_setting_obj.setting}, Updating to {vt_scan_retention_period} days...")
        existing_setting_obj.setting = vt_scan_retention_period
        existing_setting_obj.save()
    elif existing_setting_obj:
        current_app.logger.info(f"Virus Total scan retention period already exists and is set to {existing_setting_obj.setting} days, Skipping...")
    else:
        settings_obj = Settings.create(name='vt_scan_retention_period', setting=vt_scan_retention_period)
        current_app.logger.info(f"Virus Total scan retention period doesn't exists, Creating it to {vt_scan_retention_period} days...")
        add_or_update_cached_setting(setting_obj=settings_obj)


@click.option("--vt_scan_retention_period", help="Virus total scan retention period")
@app.cli.command("update_vt_scan_retention_period", help="Updates the Virus Total scan retention period")
def update_vt_scan_retention_period_command(vt_scan_retention_period):
    update_vt_scan_retention_period(vt_scan_retention_period)


def update_settings(data_retention_days, alert_aggregation_duration):
    from polylogyx.utils.cache import refresh_cached_settings
    if not (0 < int(data_retention_days) < int(current_app.config.get('INI_CONFIG', {}).get('max_data_retention_days'))):
        current_app.logger.info(f"Data retention days should be greater than 0 and less than {current_app.config.get('INI_CONFIG', {}).get('max_data_retention_days')}...")
        data_retention_days = current_app.config.get('INI_CONFIG', {}).get('max_data_retention_days')
    data_retention_setting = Settings.query.filter(
        Settings.name == "data_retention_days"
    ).first()
    alert_aggr_dur_setting = Settings.query.filter(
        Settings.name == "alert_aggregation_duration"
    ).first()

    if data_retention_setting and override_default_data:
        current_app.logger.info(f"Data retention period already exists and is set to {data_retention_setting.setting}, Updating to {data_retention_days} days...")
        data_retention_setting.setting = data_retention_days
        data_retention_setting.save()
    elif data_retention_setting:
        current_app.logger.info(f"Data retention period already exists and is set to {data_retention_setting.setting}, Skipping...")
    else:
        current_app.logger.info(f"Data retention period doesn't exists, Creating it to {data_retention_days} days...")
        Settings.create(name='data_retention_days', setting=data_retention_days)

    if alert_aggr_dur_setting and override_default_data:
        current_app.logger.info(f"Alert aggregation duration already exists and is set to {alert_aggr_dur_setting.setting}, Updating to {alert_aggregation_duration} secs...")
        alert_aggr_dur_setting.setting = alert_aggregation_duration
        alert_aggr_dur_setting.save()
    elif alert_aggr_dur_setting:
        current_app.logger.info(f"Alert aggregation duration already exists and is set to {alert_aggr_dur_setting.setting}, Skipping...")
    else:
        current_app.logger.info(f"Alert aggregation duration doesn't exists, Creating it to {alert_aggregation_duration} secs...")
        Settings.create(name='alert_aggregation_duration', setting=alert_aggregation_duration)
    refresh_cached_settings()


@click.option("--data_retention_days", default=7, help="Duration to retain platform data and drop the older data")
@click.option("--alert_aggregation_duration", default=60,
              help="Interval to aggregate the event to an alert if it's matching with the same rule & from same host")
@app.cli.command("update_settings", help="Updates settings that are being used in the platform")
def update_settings_command(data_retention_days, alert_aggregation_duration):
    update_settings(data_retention_days, alert_aggregation_duration)


def add_role(name, description, access_level):
    if Role.query.filter(or_(Role.name == name, Role.access_level == access_level)).first():
        current_app.logger.error("Role with this name or access level already exists!")
        exit(1)
    try:
        Role.create(name=name, access_level=access_level, description=description)
    except Exception as error:
        current_app.logger.error("Failed to create role '{0}' - {1}".format(name, error))
        exit(1)
    else:
        current_app.logger.info("Created role '{0}'".format(name))
        exit(0)


@click.argument('name')
@click.option("--description", default=None, help="Description of the role")
@click.option('--access_level', help="Access level of the role")
@app.cli.command("add_role", help="Adds a platform user role")
def add_role_command(name, description, access_level):
    add_role(name, description, access_level)


def add_user(username, password, email=None, role=None, first_name=None, last_name=None):
    existing_user = User.query.filter(User.username == username).first()
    if role:
        role_object = Role.query.filter(Role.name == role).first()
        if not role_object:
            current_app.logger.error("Role '{0}' requested for assignment does not exists! "
                                     "Please create one or pass correct role name".format(role))
            exit(1)
    else:
        role_object = None

    if existing_user:
        current_app.logger.info("User with this username already exists!")
        if role_object and not existing_user.roles:
            existing_user.update(roles=[role_object], reset_password=True, status=True, enable_sso=True,
                                 reset_email=True)
    else:
        try:
            user = User.create(username=username, email=email,
                               password=password, first_name=first_name, last_name=last_name,
                               roles=[role_object], groups=[], reset_password=True, status=True, enable_sso=True,
                               reset_email=True)
        except Exception as error:
            current_app.logger.error("Failed to create user '{0}' - {1}".format(username, error))
            exit(1)
        else:
            current_app.logger.info("Created user '{0}'".format(user.username))
            exit(0)


@click.argument('username')
@click.option('--password', help="Password of the user")
@click.option("--email", default=None, help="Email of the user")
@click.option('--role', help="Role to apply to the user")
@click.option("--first_name", default=None, help="First name of the user")
@click.option("--last_name", default=None, help="Last name of the user")
@app.cli.command("add_user", help="Adds a new user")
def add_user_command(username, password, email=None, role=None, first_name=None, last_name=None):
    add_user(username, password, email, role, first_name, last_name)


def update_role_for_existing_users():
    default_roles = current_app.config.get('DEFAULT_ROLES', {})
    if isinstance(default_roles, dict):
        admin_role = default_roles[min(default_roles.keys())]
        role_object = Role.query.filter(Role.name == admin_role).first()
        if role_object:
            users = User.query.all()
            for user in users:
                if not user.roles:
                    user.update(roles=[role_object], reset_password=True, status=True, enable_sso=True,
                                reset_email=True)
                    current_app.logger.info("Successfully updated role for user '{0}'".format(user.username))
        else:
            current_app.logger.info("Role '{0}' does not exists, Please create one before user update!"
                                    .format(role_object))
    else:
        current_app.logger.error("Default roles set are not in dict format, Please pass a dict of roles!")
        exit(1)
    exit(0)


@app.cli.command('update_role_for_existing_users',
                 help="Updates role to all the users prior to the platform version 3.5.0")
def update_role_for_existing_users_command():
    update_role_for_existing_users()


def create_all_roles():
    default_roles = current_app.config.get('DEFAULT_ROLES', {})
    if isinstance(default_roles, dict):
        for access_level, role in default_roles.items():
            try:
                existing_role = Role.query.filter(or_(Role.name == role, Role.access_level == access_level)).first()
                if not existing_role:
                    role = Role.create(name=role, access_level=access_level, description=role)
                    current_app.logger.info("Role '{0}' does not exists, Creating new...".format(role))
                else:
                    current_app.logger.error("Role '{0}' exists, Skipping...".format(role))
            except Exception as error:
                current_app.logger.error("Failed to create role '{0}' - {1}".format(role, error))
                exit(1)
    else:
        current_app.logger.error("Default roles set are not in dict format, Please pass a dict of roles!")
        exit(1)


@app.cli.command('create_all_roles', help="Creates all the roles of the platform users")
def create_all_roles_command():
    create_all_roles()


def update_user(username, password, email=None, role=None, first_name=None, last_name=None):
    user = User.query.filter(or_(User.username == username, User.email == username)).first()
    if not user:
        current_app.logger.error("User with this username doesn't exists!")
        exit(1)
    try:
        user.update(status=True)
        if password:
            user.update(password=bcrypt.generate_password_hash(password.encode("utf-8")).decode("utf-8"),
                        reset_password=True)
        if email:
            user.update(email=email)
        if first_name:
            user.update(first_name=first_name)
        if last_name:
            user.update(last_name=last_name)
        if role:
            existing_role = Role.query.filter(Role.name == role).first()
            if existing_role and not user.roles:
                user.update(roles=[existing_role], reset_password=True, status=True, enable_sso=True, reset_email=True)
            else:
                current_app.logger.info("Role '{0}' does not exists, Please create one before user update!"
                                        .format(role))
        current_app.logger.info("Successfully updated password for user '{0}'".format(user.username))

    except Exception as error:
        current_app.logger.info("Failed to create user '{0}' - {1}".format(username, error))
        exit(1)
    exit(0)


@click.argument('username')
@click.option('--password', default=None, help="Password of the user")
@click.option("--email", default=None, help="Email of the user")
@click.option('--role', help="Role to apply to the user")
@click.option("--first_name", default=None, help="First name of the user")
@click.option("--last_name", default=None, help="Last name of the user")
@app.cli.command('update_user', help="Updates a platform user")
def update_user_command(username, password=None, email=None, role=None, first_name=None, last_name=None):
    update_user(username, password, email, role, first_name, last_name)


def extract_ddl(specs_dir, export_type, target_file):
    """
    Extracts CREATE TABLE statements or JSON Array of schema from osquery's table specifications

    flask extract_ddl --specs_dir /Users/polylogyx/osquery/specs --export_type sql
            ----> to export to osquery_schema.sql file
    flask extract_ddl --specs_dir /Users/polylogyx/osquery/specs --export_type json
            ----> to export to osquery_schema.json file
    """
    from polylogyx.db.extract_ddl import extract_schema, extract_schema_json

    current_app.logger.info("Importing OSQuery Schema to json/sql format...")
    spec_files = []
    spec_files.extend(glob.glob(join(specs_dir, '*.table')))
    spec_files.extend(glob.glob(join(specs_dir, '**', '*.table')))
    if export_type == 'sql':
        ddl = sorted([extract_schema(f) for f in spec_files], key=lambda x: x.split()[2])
        opath = join(current_app.config.get('COMMON_FILES_URL', ''), target_file)
        content = '\n'.join(ddl)
    elif export_type == 'json':
        full_schema = []
        for f in spec_files:
            table_dict = extract_schema_json(f)
            if table_dict["platform"]:
                full_schema.append(table_dict)
        opath = join(current_app.config.get('COMMON_FILES_URL', ''), target_file)
        content = json.dumps(full_schema)
    else:
        print("Export type given is invalid!")
        opath = None
        content = None

    with open(opath, "w") as f:
        if export_type == "sql":
            f.write(
                '-- This file is generated using "flask extract_ddl"'
                "- do not edit manually\n"
            )
        f.write(content)
    current_app.logger.info('OSQuery Schema is exported to the file {} successfully'.format(opath))


@click.option('--specs_dir', help="Osquery specs directory path")
@click.option("--export_type", default='sql', help="sql to export as sql file, json to export to json file")
@click.option("--target_file", default='osquery_schema.sql', help="Target file path to write the schema")
@app.cli.command('extract_ddl', help="Extracts the osquery schema to a json/sql file")
def extract_ddl_command(specs_dir, export_type, target_file):
    extract_ddl(specs_dir, export_type, target_file)


def update_osquery_schema(file_path):
    from polylogyx.db.models import OsquerySchema

    # Delete the old schema as there were optimized tables populated in previous releases
    current_app.logger.info(
        "Importing OSQuery Schema json to 'OsquerySchema' table from the file path '{0}'".format(file_path))
    OsquerySchema.query.delete()
    try:
        f = open(file_path, "r")
    except FileNotFoundError:
        print("File is not present for the path given!")
        exit(0)
    except Exception as e:
        print(str(e))
        exit(0)

    file_content = f.read()
    schema_json = json.loads(file_content)
    for table_dict in schema_json:
        table = OsquerySchema.query.filter(
            OsquerySchema.name == table_dict["name"]
        ).first()
        if table:
            if not table.name.endswith("_optimized"):
                table.update(schema=table_dict['schema'], description=table_dict['description'],
                             platform=table_dict['platform'])
            else:
                table.delete()
        else:
            if not table_dict['platform'] == ['freebsd'] and not table_dict['platform'] == ['posix'] and \
                    not table_dict['name'].endswith("_optimized"):
                OsquerySchema.create(name=table_dict['name'], schema=table_dict['schema'],
                                     description=table_dict['description'], platform=table_dict['platform'])
    current_app.logger.info('OsQuery Schema is updated to postgres through the file input {} successfully'
                            .format(file_path))
    exit(0)


@click.option("--file_path", default="/src/plgx-esp/common/osquery_schema.json",
              help="Absolute/Relative file path of os query schema json file")
@app.cli.command('update_osquery_schema', help="Updates the osquery schema into database for live query page use")
def update_osquery_schema_command(file_path):
    update_osquery_schema(file_path)


def add_result_log_map_data(partition):
    # mapping result_scan_id and result_log ids for existing data
    db.session.execute('''
            INSERT INTO RESULT_LOG_MAPS
                (SELECT A.R_ID,B.RS_ID
                FROM
                    (SELECT RS.ID RS_ID,RS.SCAN_VALUE MD5_RS
                    FROM 
                        RESULT_LOG_SCAN RS
                    WHERE SCAN_TYPE = 'md5'
                    ) B,
                    (SELECT *
                    FROM
                        (SELECT R.COLUMNS ->> 'md5' MD5_R,R.ID R_ID
                        FROM 
                            {0} R
                        ) RL
                        WHERE RL.MD5_R IS NOT NULL)A
                WHERE B.MD5_RS = A.MD5_R
                );
                '''.format(partition))
    db.session.commit()


def add_partitions_existing_data():
    import datetime
    partition_dates = db.session.execute('select timestamp::date from result_log_old group by timestamp::date order by timestamp DESC;')
    db.session.commit()
    delete_setting=Settings.query.filter(Settings.name == 'data_retention_days').first()
    drop_date = datetime.date.today() - dt.timedelta(hours=24 * (int(delete_setting.setting)))
    partition_dates =[partition_date[0] for partition_date in partition_dates]
    start_time = datetime.datetime.utcnow()
    today=datetime.date.today()
    for partition_date in partition_dates:
         if partition_date != today and partition_date >= drop_date:
            create_partition_from_old_data(partition_date)
    end_time = datetime.datetime.utcnow()
    print('Time took to complete', end_time-start_time)
    db.session.commit()
    current_app.logger.info('Updating result log scans and result log data to result map')


@app.cli.command('add_partitions_existing_data', help="Creates partitions for the existing data, prior to 3.5.0")
def add_partitions_existing_data_command():
    add_partitions_existing_data()


def check_table_exists(tbl_name):
    check_if_trigger_exists = "select count(*) from pg_tables where lower(tablename)='{}'".format(tbl_name.lower())
    res = db.session.execute(check_if_trigger_exists).first()[0]
    db.session.rollback()
    if res == 0:
        return False
    else:
        return True


def create_partition_from_old_data(partition_date=dt.date.today()):
    start_date = partition_date.strftime("%b-%d-%Y").split("-")
    end_date = (partition_date + dt.timedelta(days=1))
    month = start_date[0]
    date = start_date[1]
    year = start_date[2]
    result_log_partition_table = ('result_log_' + str(month) + "_" + str(date) + "_" + str(year))
    node_query_count_partition_table = ("node_query_count_" + str(month) + "_" + str(date) + "_" + str(year))

    if not check_table_exists("result_log_old"):
        print("Backup table does not exists")
        return

    if check_table_exists(result_log_partition_table):
        print("Partition {} already exists, hence not creating it from backup".format(result_log_partition_table))
        return

    try:
        start_time = dt.datetime.utcnow()
        print('Creating partition - {}'.format(result_log_partition_table))
        sql = "CREATE TABLE {0} AS SELECT * FROM result_log_old WHERE timestamp::date >= '{1}' AND timestamp::date < '{2}';".format(
            result_log_partition_table, partition_date, end_date)
        db.session.execute(sql)
        constraint_sql = "alter table {0} alter column id set not null," \
                         "alter column name set not null,alter column node_id set not null;".format(
            result_log_partition_table)
        db.session.execute(constraint_sql)
        set_created_at = "update {0} set created_at=timestamp;".format(result_log_partition_table)
        db.session.execute(set_created_at)
        set_query_name = "update {0} set name='windows_real_time_events' where name='windows_events';".format(
            result_log_partition_table)
        db.session.execute(set_query_name)
        attach_sql = "alter table result_log attach partition {0} for values from ('{1}') to ('{2}');".format(
            result_log_partition_table, partition_date, end_date)
        db.session.execute(attach_sql)
        update_node_query_count = "INSERT INTO node_query_count(total_results,node_id,query_name,event_id,date)" \
                                  " SELECT count(*),node_id,name,columns->>'eventid',created_at::date " \
                                  "FROM {0} group by name,node_id,columns->>'eventid',created_at::date;".format(
            result_log_partition_table)

        db.session.execute(update_node_query_count)
        db.session.commit()
        create_index_for_result_log(result_log_partition_table)
        add_result_log_map_data(result_log_partition_table)
        end_time = dt.datetime.utcnow()
        current_app.logger.info('Added partition for {}'.format(result_log_partition_table))
    except Exception as e:
        db.session.rollback()
        current_app.logger.info(e)


@app.cli.command('create_partition_from_old_data', help="Creates partitions from old data")
def create_partition_from_old_data_command(partition_date=dt.date.today()):
    create_partition_from_old_data(partition_date)


def drop_old_data():
    db.session.execute('drop table result_log_old;')
    db.session.execute('drop table node_query_count_old;')
    db.session.commit()


@app.cli.command('drop_old_data', help="Drops the back up tables created for partitions creation")
def drop_old_data_command():
    drop_old_data()


def set_log_level(log_level):
    if not _check_log_level_exists():
        _set_log_level_to_db(log_level)


from polylogyx.utils.log_setting import _set_log_level_to_db, _check_log_level_exists
@click.option("--log_level", default="WARNING", help="Log level that application server uses to log")
@app.cli.command('set_log_level', help="Updates the er server log level")
def set_log_level_command(log_level):
    set_log_level(log_level)


def add_api_key(IBMxForceKey, IBMxForcePass, VT_API_KEY, OTX_API_KEY):
    virus_total = ibm_x_force = alien_vault = None
    virus_total_creds = alien_vault_creds = ibm_x_force_creds = None
    intels = ThreatIntelCredentials.query.filter(ThreatIntelCredentials.intel_name.in_(('ibmxforce', 'virustotal', 'alienvault'))).all()
    for intel in intels:
        if intel.intel_name == 'ibmxforce':
            ibm_x_force = intel
        elif intel.intel_name == 'virustotal':
            virus_total = intel
        else:
            alien_vault = intel
            
    if VT_API_KEY:
        virus_total_creds = {'key': VT_API_KEY}
    if IBMxForceKey and IBMxForcePass:
        ibm_x_force_creds = {'key': IBMxForceKey, 'pass': IBMxForcePass}
    if OTX_API_KEY:
        alien_vault_creds = {'key': OTX_API_KEY}

    if virus_total_creds:
        if virus_total and override_default_data:
            current_app.logger.info('Virus Total Key already exists, Updating...')
            virus_total.credentials = virus_total_creds
            virus_total.save()
        elif virus_total:
            current_app.logger.info('Virus Total Key already exists, Skipping...')
        else:
            current_app.logger.info("Virus Total Key doesn't exists, Creating...")
            ThreatIntelCredentials.create(intel_name='virustotal', credentials=virus_total_creds)

    if alien_vault_creds:
        if alien_vault and override_default_data:
            current_app.logger.info('Alien Vault OTX Key already exists, Updating...')
            alien_vault.credentials = alien_vault_creds
            alien_vault.save()
        elif alien_vault:
            current_app.logger.info('Alien Vault OTX Key already exists, Skipping...')
        else:
            current_app.logger.info("Alien Vault OTX Key doesn't exists, Creating...")
            ThreatIntelCredentials.create(intel_name='alienvault', credentials=alien_vault_creds)
    
    if ibm_x_force_creds:
        if ibm_x_force and override_default_data:
            current_app.logger.info('IBM X Force Key already exists, Updating...')
            ibm_x_force.credentials = ibm_x_force_creds
            ibm_x_force.save()
        elif ibm_x_force:
            current_app.logger.info('IBM X Force Key already exists, Skipping...')
        else:
            current_app.logger.info("IBM X Force Key doesn't exists, Creating...")
            ThreatIntelCredentials.create(intel_name='ibmxforce', credentials=ibm_x_force_creds)


@click.option("--ibm_x_force_key", default=None, help="IBMxForce Key for Threat Intel Matching")
@click.option("--ibm_x_force_pass", default=None, help="IBMxForce Pass for Threat Intel Matching")
@click.option("--vt_key", default=None, help="Virus Total API KEY for Threat Intel Matching")
@click.option("--otx_key", default=None, help="Alient Vault OTX API KEY for Threat Intel Matching")
@app.cli.command('add_api_key', help="Updating Threat Intel keys")
def add_api_key_command(ibm_x_force_key, ibm_x_force_pass, vt_key, otx_key):
    add_api_key(ibm_x_force_key, ibm_x_force_pass, vt_key, otx_key)


if __name__ == '__main__':
    if CurrentConfig == DevConfig:
        ssl_context = ('../nginx/certificate.crt', '../nginx/private.key')
        app.run(debug=True, use_debugger=True, use_reloader=False, passthrough_errors=True,
                host='0.0.0.0', port=9000,
                ssl_context=ssl_context,
                )
    elif CurrentConfig == TestConfig:
        test(['tests/'])
    else:
        print("""
        Please set ENV env variable correctly!
        for production env -- 'export ENV=prod'
        for test env -- 'export ENV=test'
        """)
        exit(1)
