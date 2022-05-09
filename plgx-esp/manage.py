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
import sys
from os.path import abspath, dirname, join

from flask import json, current_app, jsonify, request
from flask_migrate import MigrateCommand
from flask_script import Command, Manager, Server, Shell
from flask_script.commands import Clean, ShowUrls
from sqlalchemy import or_
from werkzeug.contrib.fixers import ProxyFix

from polylogyx import create_app, db
from polylogyx.constants import (DefaultInfoQueries, PolyLogyxConstants,
                                 PolyLogyxServerDefaults, UtilQueries)
from polylogyx.extensions import bcrypt
from polylogyx.db.models import Query, Rule, Options, Settings, DefaultFilters, DefaultQuery, Config, \
    VirusTotalAvEngines, ResultLog, ResultLogScan
from polylogyx.settings import CurrentConfig
from polylogyx.constants import PolyLogyxServerDefaults, UtilQueries, PolyLogyxConstants, DefaultInfoQueries
from werkzeug.contrib.fixers import ProxyFix
import sys

from polylogyx.celery.tasks import create_daily_partition ,create_index_and_trigger
from polylogyx.db.models import Query, Rule, Options, Settings, DefaultFilters, DefaultQuery, Config, \
    VirusTotalAvEngines, ResultLog, ResultLogScan, Role, User, Pack, ReleasedAgentVersions, OsquerySchema
from polylogyx.settings import CurrentConfig
from polylogyx.constants import PolyLogyxServerDefaults, UtilQueries, PolyLogyxConstants, DefaultInfoQueries
from polylogyx.celery.tasks import create_daily_partition


app = create_app(config=CurrentConfig)
app.wsgi_app = ProxyFix(app.wsgi_app)


def _make_context(): # pragma: no cover
    return {"app": app, "db": db}


class SSLServer(Command): # pragma: no cover
    def run(self, *args, **kwargs):
        ssl_context = ('../nginx/certificate.crt', '../nginx/private.key')
        app.run(debug=True, use_debugger=True, use_reloader=False, passthrough_errors=True,
                host='0.0.0.0', port=9001,
                ssl_context=ssl_context,
                *args, **kwargs)


manager = Manager(app)
manager.add_command("server", Server())

manager.add_command("shell", Shell(make_context=_make_context))
manager.add_command("db", MigrateCommand)
manager.add_command("clean", Clean())
manager.add_command("urls", ShowUrls())
manager.add_command("ssl", SSLServer())


@app.before_request
def before_request_method(): # pragma: no cover
    from polylogyx.utils.cache import get_average_celery_task_wait_time,get_log_level
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
        set_app_log_level(get_log_level())
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


@manager.add_command
class test(Command):
    name = "test"
    capture_all_args = True

    def run(self, remaining):
        import pytest

        test_path = join(abspath(dirname(__file__)), "tests")

        if remaining:
            test_args = remaining + ["--verbose"]
        else:
            test_args = [test_path, "--verbose"]

        exit_code = pytest.main(test_args)
        return exit_code


@manager.option("--filepath")
@manager.option("--platform")
@manager.option("--name")
@manager.option("--is_default", default=False, type=bool)
def add_default_filters(filepath, platform, name, is_default):
    current_app.logger.info("Adding default filters for config with name '{0}' and with platform '{1}'...".format(name, platform))
    current_app.logger.debug("Received filters json file path is:\n '{0}'".format(filepath))
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
            "Created a new config '{0}' to add the filters provided...".format(config))
    else:
        config.update(is_default=is_default, description=description)
        current_app.logger.info(
            "Updating the existing config '{0}' to add/update the filters provided...".format(config))
    existing_filter = DefaultFilters.query.filter_by(platform=platform, config_id=config.id).first()
    try:
        json_str = open(filepath, 'r').read()
        filter = json.loads(json_str)
        current_app.logger.debug("Received filters json payload is:\n '{0}'".format(filter))
        if existing_filter:
            existing_filter.filters = filter
            existing_filter.update(existing_filter)
            current_app.logger.info("Filter already exists updating...")
        else:
            current_app.logger.info("Filter does not exist, adding new...")
            DefaultFilters.create(filters=filter, platform=platform, created_at=dt.datetime.utcnow(),
                                  config_id=config.id)
        config.update(updated_at=dt.datetime.utcnow())
    except Exception as error:
        current_app.logger.error(str(error))


@manager.command
def delete_existing_unmapped_queries_filters():
    current_app.logger.info("Deleting the existing unmapped Queries and Filters...")
    db.session.query(DefaultQuery).filter(DefaultQuery.config_id == None).delete()
    db.session.query(DefaultFilters).filter(DefaultFilters.config_id == None).delete()
    db.session.commit()


@manager.option("--filepath")
@manager.option("--platform")
@manager.option("--name")
@manager.option("--is_default", default=False, type=bool)
def add_default_queries(filepath, platform, name, is_default):
    current_app.logger.debug("Received queries json file path is:\n '{0}'".format(filepath))
    try:
        if is_default:
            description = "Default configuration of {0} hosts".format(platform)
        else:
            description = "A Sample configuration with suggested queries and filters to monitor host state"
        current_app.logger.info("Adding default queries for config with name '{0}' and with platform '{1}'..."
                                .format(name, platform))
        json_str = open(filepath, 'r').read()
        query = json.loads(json_str)
        current_app.logger.debug("Received queries json payload is:\n '{0}'".format(query))
        queries = query['schedule']
        config = db.session.query(Config).filter(Config.name == name).filter(Config.platform == platform).first()
        if config:
            DefaultQuery.query.filter(DefaultQuery.config_id == config.id).filter(
                ~DefaultQuery.name.in_(queries.keys())
            ).delete(synchronize_session=False)
            config.update(is_default=is_default, description=description)
        else:
            config = Config.create(platform=platform, name=name, is_default=is_default, description=description)
        for query_key in queries.keys():
            if query_key not in DefaultInfoQueries.DEFAULT_VERSION_INFO_QUERIES.keys():
                query_filter = DefaultQuery.query.filter_by(platform=platform).filter_by(name=query_key)\
                    .filter_by(config_id=config.id)
                config_id = config.id
            else:
                query_filter = DefaultQuery.query.filter_by(
                    platform=platform
                ).filter_by(name=query_key)
                config_id = None
            query = query_filter.first()
            try:
                if "snapshot" in queries[query_key]:
                    snapshot = queries[query_key]["snapshot"]
                else:
                    snapshot = False

                if query:
                    sys.stderr.write(
                        "Query name " + query_key + " already exists, updating..!"
                    )
                    query.sql = queries[query_key]["query"]
                    query.interval = queries[query_key]["interval"]
                    query.status = queries[query_key]["status"]
                    query.snapshot = snapshot
                    query.update(query)
                else:
                    sys.stderr.write(query_key + " does not exist, adding new...")
                    status = True
                    if "status" in queries[query_key]:
                        status = queries[query_key]["status"]

                    DefaultQuery.create(
                        name=query_key,
                        sql=queries[query_key]["query"],
                        config_id=config_id,
                        interval=queries[query_key]["interval"],
                        status=status,
                        platform=platform,
                        description=queries[query_key].get("description"),
                        snapshot=snapshot,
                    )
            except Exception as error:
                sys.stderr.write(str(error))
        config.update(updated_at=dt.datetime.utcnow())
    except Exception as error:
        raise (str(error))

@manager.command
def update_query_name_for_custom_config():
    configs = db.session.query(Config).filter(Config.platform == 'windows').all()
    for config in configs:
        default_query = DefaultQuery.query.filter(DefaultQuery.config_id == config.id).\
            filter(DefaultQuery.name == 'windows_events').first()
        if default_query:
            default_query.update(name='windows_real_time_events')
    db.session.commit()


@manager.option("packname")
@manager.option("--filepath")
def addpack(packname, filepath): # pragma: no cover
    from polylogyx.db.models import Pack

    current_app.logger.debug("Received pack file from the path '{0}' and pack name '{1}'".format(filepath, packname))
    existing_pack = Pack.query.filter_by(name=packname).first()
    try:
        json_str = open(filepath, 'r').read()
        data = json.loads(json_str)
        current_app.logger.debug("Received pack json is \n'{0}'".format(data))
        if not existing_pack:
            pack = Pack.create(name=packname)
        else:
            pack = existing_pack
            current_app.logger.info(
                "Pack with name '{0}' already exists!".format(packname))
        current_app.logger.info("Created a new pack '{0}'".format(packname))
        for query_name, query in data['queries'].items():
            q = Query.query.filter(Query.name == query_name).first()

            if not q:
                q = Query.create(name=query_name, **query)
                pack.queries.append(q)
                current_app.logger.info("Adding new query {0} to pack {1}".format(q.name, pack.name))
                continue

            if q in pack.queries:
                continue

            if q.sql == query['query']:
                current_app.logger.info("Adding existing query {0} to pack {1}".format(q.name, pack.name))
                pack.queries.append(q)
            else:
                q2 = Query.create(name=query_name, **query)
                current_app.logger.info("Created another query named {0}, but different sql: {1} vs {2}"
                                        .format(query_name, q2.sql.encode('utf-8'), q.sql.encode('utf-8')))
                pack.queries.append(q2)
        pack.save()
    except Exception as error:
        current_app.logger.error("Failed to create pack {0} - {1}".format(packname, error))
        exit(1)
    else:
        current_app.logger.info("Created pack {0}".format(pack.name))
        exit(0)


@manager.command
def add_partition():
    for i in range(7):
        create_daily_partition(day_delay=i)


@manager.option('--filepath')
def add_rules(filepath):
    with open(filepath) as f:
        rules = json.load(f)

    current_app.logger.debug("Adding default rules from the path '{0}' ...".format(filepath))

    for name, data in rules.items():
        rule = Rule.query.filter_by(name=data["name"]).first()
        if rule:
            current_app.logger.debug("Updating rule '{0}' from the json: \n'{1}' ...".format(rule, data))
            sys.stderr.write('Updating rule.. ' + rule.name)
            rule.platform = data.get('platform')
            rule.description = data['description']
            rule.conditions = data['conditions'],
            rule.conditions = rule.conditions[0]
            rule.status = data.get('status', Rule.ACTIVE)
            rule.alert_description = data.get('alert_description', False)

            if "technique_id" in data:
                if data["technique_id"]:
                    rule.tactics = data["tactics"]
                    rule.technique_id = data["technique_id"]
                    if "type" not in data:
                        rule.type = Rule.MITRE
                    else:
                        rule.type = data["type"]
                    rule.save(rule)
        else:
            sys.stderr.write('Creating rule.. ' + data['name'])
            current_app.logger.debug("Creating a new rule '{0}' from the json: \n'{1}' ...".format(data['name'], data))
            severity = Rule.WARNING
            try:
                if data['severity']:
                    severity = data['severity']
            except Exception as e:
                current_app.logger.error("Unable to find the severity from json - {0}".format(str(e)))
            if 'technique_id' in data:
                if data['technique_id']:
                    rule = Rule(name=data['name'],
                                platform=data.get('platform', 'windows'),
                                alert_description=data.get('alert_description', False),
                                alerters=data['alerters'],
                                description=data['description'],
                                conditions=data['conditions'],
                                status=data.get('status', Rule.ACTIVE),
                                technique_id=data['technique_id'],
                                tactics=data['tactics'],
                                severity=severity,
                                type=Rule.MITRE,
                                recon_queries=json.dumps(UtilQueries.ALERT_RECON_QUERIES_JSON))
            else:
                rule = Rule(name=data['name'],
                            platform=data.get('platform', 'windows'),
                            alert_description=data.get('alert_description', False),
                            alerters=data['alerters'],
                            description=data['description'],
                            conditions=data['conditions'],
                            status=data.get('status', Rule.ACTIVE),
                            severity=severity,
                            recon_queries=json.dumps(UtilQueries.ALERT_RECON_QUERIES_JSON))
            rule.save()


@manager.option('--filepath')
def add_default_vt_av_engines(filepath):
    try:
        sys.stderr.write('Adding Virus total AntiVirus engines')
        json_str = open(filepath, 'r').read()
        av_engine = json.loads(json_str)
        current_app.logger.debug(
            "Adding/Updating VirusTotal AV Engines info from the json data:\n {0}".format(av_engine))
        av_engines = av_engine['av_engines']
        for key in av_engines.keys():
            av_engine_obj = VirusTotalAvEngines.query.filter(VirusTotalAvEngines.name == key).first()
            if av_engine_obj:
                current_app.logger.info(" Virus total AntiVirus engine {0} is already present ".format(av_engine_obj))
            else:
                VirusTotalAvEngines.create(name=key, status=av_engines[key]["status"])
    except Exception as error:
        current_app.logger.error("Error updating default VirusTotal AV Engines info - {0}".format(str(error)))
    db.session.commit()


@manager.option("--vt_min_match_count")
def update_vt_match_count(vt_min_match_count):
    existing_setting_obj = Settings.query.filter(Settings.name == 'virustotal_min_match_count').first()
    if existing_setting_obj:
        current_app.logger.info(
            "VT min match count is already set from existing Settings Object '{0}'".format(existing_setting_obj))
    else:
        settings_obj = Settings.create(name='virustotal_min_match_count', setting=vt_min_match_count)
        current_app.logger.info(
            "VT min match count was not set, so creating a new Settings Object '{0}'".format(settings_obj))


@manager.option("--vt_scan_retention_period")
def update_vt_scan_retention_period(vt_scan_retention_period):
    existing_setting_obj = Settings.query.filter(Settings.name == 'vt_scan_retention_period').first()
    if existing_setting_obj:
        current_app.logger.info(
            "vt scan retention period is already set from existing Settings Object '{0}'".format(existing_setting_obj))
    else:
        settings_obj = Settings.create(name='vt_scan_retention_period', setting=vt_scan_retention_period)
        current_app.logger.info(
            "vt scan retention period  was not set, so creating a new Settings Object '{0}'".format(settings_obj))


@manager.option("--data_retention_days", default=7)
@manager.option("--alert_aggregation_duration", default=60)
def update_settings(data_retention_days, alert_aggregation_duration):
    data_retention_setting = Settings.query.filter(
        Settings.name == "data_retention_days"
    ).first()
    alert_aggr_dur_setting = Settings.query.filter(
        Settings.name == "alert_aggregation_duration"
    ).first()

    if data_retention_setting:
        current_app.logger.info("Purge duration is already set to {0} days, Updating it..."
                                .format(data_retention_setting.setting))
    else:
        current_app.logger.info("Setting up Purge duration to {0} days...".format(data_retention_days))
        Settings.create(name='data_retention_days', setting=data_retention_days)

    if alert_aggr_dur_setting:
        current_app.logger.info("Alert aggregation duration is already set to {0} seconds, Updating it..."
                                .format(alert_aggr_dur_setting.setting))
        alert_aggr_dur_setting.update(setting=alert_aggregation_duration)
    else:
        current_app.logger.info("Setting up Alert aggregation duration to {0} seconds..."
                                .format(alert_aggregation_duration))
        Settings.create(name='alert_aggregation_duration', setting=alert_aggregation_duration)

    


@manager.option('--name')
@manager.option('--description', default=None)
@manager.option('--access_level', default=None, type=int)
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


@manager.option('username')
@manager.option('--password', default=None)
@manager.option('--email', default=None)
@manager.option('--role')
@manager.option('--first_name', default=None)
@manager.option('--last_name', default=None)
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
        current_app.logger.error("User with this username already exists!")
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


@manager.command
def add_admin_user():
    default_roles = current_app.config.get('DEFAULT_ROLES', {})
    if isinstance(default_roles, dict):
        admin_role = default_roles[min(default_roles.keys())]
        username = os.environ.get('POLYLOGYX_USER', 'admin')
        password = os.environ.get('POLYLOGYX_PASSWORD', 'admin')
        email = os.environ.get('POLYLOGYX_USER_EMAIL')
        first_name = os.environ.get('POLYLOGYX_USER_FIRST_NAME')
        last_name = os.environ.get('POLYLOGYX_USER_LAST_NAME')
        add_user(username=username, password=password, role=admin_role, email=email, first_name=first_name,
                 last_name=last_name)


@manager.command
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


@manager.command
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


@manager.option('--username')
@manager.option('--password', default=None)
@manager.option('--email', default=None)
@manager.option('--role', default=None)
@manager.option('--first_name', default=None)
@manager.option('--last_name', default=None)
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


@manager.option("--filepath")
def add_release_versions(filepath):
    from polylogyx.db.models import ReleasedAgentVersions

    current_app.logger.info("Adding/Updating Platform release history")
    json_str = open(filepath, 'r').read()
    data = json.loads(json_str)
    current_app.logger.debug("Received platform release history data:\n{0}".format(data))
    for release_version, rel_dict in data.items():
        for platform, platform_dict in rel_dict.items():
            for arch, arch_dict in platform_dict.items():
                agent_version_history = (
                    ReleasedAgentVersions.query.filter(
                        ReleasedAgentVersions.platform == platform
                    )
                    .filter(ReleasedAgentVersions.arch == arch)
                    .filter(ReleasedAgentVersions.platform_release == release_version)
                    .first()
                )
                extension_version = arch_dict.get("extension", {}).get("version", None)
                extension_hash_md5 = arch_dict.get("extension", {}).get("md5", None)
                cpt_version = arch_dict.get("cpt", {}).get("version", None)
                cpt_hash_md5 = arch_dict.get("cpt", {}).get("md5", None)
                osquery_version = arch_dict.get("osquery", {}).get("version", None)
                osquery_hash_md5 = arch_dict.get("osquery", {}).get("md5", None)
                if agent_version_history:
                    agent_version_history.extension_version = extension_version
                    agent_version_history.extension_hash_md5 = extension_hash_md5
                    agent_version_history.cpt_version = cpt_version
                    agent_version_history.cpt_hash_md5 = cpt_hash_md5
                    agent_version_history.osquery_version = osquery_version
                    agent_version_history.osquery_hash_md5 = osquery_hash_md5
                    agent_version_history.update(agent_version_history)
                else:
                    ReleasedAgentVersions.create(platform=platform, arch=arch, platform_release=release_version,
                                                 extension_version=extension_version,
                                                 extension_hash_md5=extension_hash_md5,
                                                 osquery_version=osquery_version, osquery_hash_md5=osquery_hash_md5,
                                                 cpt_version=cpt_version, cpt_hash_md5=cpt_hash_md5)


@manager.option('--specs_dir')
@manager.option('--export_type', default='sql', choices=['sql', 'json'])
@manager.option('--target_file', default='osquery_schema.sql')
def extract_ddl(specs_dir, export_type, target_file):
    """
    Extracts CREATE TABLE statements or JSON Array of schema from osquery's table specifications

    python manage.py extract_ddl --specs_dir /Users/polylogyx/osquery/specs --export_type sql
            ----> to export to osquery_schema.sql file
    python manage.py extract_ddl --specs_dir /Users/polylogyx/osquery/specs --export_type json
            ----> to export to osquery_schema.json file
    """
    from polylogyx.db.extract_ddl import extract_schema, extract_schema_json

    current_app.logger.info("Importing OSQuery Schema to json/sql format...")
    spec_files = []
    spec_files.extend(glob.glob(join(specs_dir, '*.table')))
    spec_files.extend(glob.glob(join(specs_dir, '**', '*.table')))
    if export_type == 'sql':
        ddl = sorted([extract_schema(f) for f in spec_files], key=lambda x: x.split()[2])
        opath = join(dirname(__file__), 'polylogyx', 'resources', target_file)
        content = '\n'.join(ddl)
    elif export_type == 'json':
        full_schema = []
        for f in spec_files:
            table_dict = extract_schema_json(f)
            if table_dict["platform"]:
                full_schema.append(table_dict)
        opath = join(dirname(__file__), 'polylogyx', 'resources', target_file)
        content = json.dumps(full_schema)
    else:
        print("Export type given is invalid!")
        opath = None
        content = None

    with open(opath, "w") as f:
        if export_type == "sql":
            f.write(
                '-- This file is generated using "python manage.py extract_ddl"'
                "- do not edit manually\n"
            )
        f.write(content)
    current_app.logger.info('OSQuery Schema is exported to the file {} successfully'.format(opath))


@manager.option("--file_path", default="polylogyx/resources/osquery_schema.json")
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


@manager.command
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
    print('Time took to complete',end_time-start_time)
    db.session.commit()
    current_app.logger.debug('Updating result log scans and result log data to result map')


def check_table_exists(tbl_name):
    check_if_trigger_exists = "select count(*) from pg_tables where lower(tablename)='{}'".format(tbl_name.lower())
    res = db.session.execute(check_if_trigger_exists).first()[0]
    db.session.rollback()
    if res==0:
        return False
    else:
        return True

@manager.command
def create_partition_from_old_data(partition_date=dt.date.today()):
    start_date=partition_date.strftime("%b-%d-%Y").split("-")
    end_date = (partition_date + dt.timedelta(days=1))
    month = start_date[0]
    date = start_date[1]
    year = start_date[2]
    result_log_partition_table=('result_log_'+str(month) + "_" + str(date) + "_" + str(year))
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
        sql = "CREATE TABLE {0} AS SELECT * FROM result_log_old WHERE timestamp::date >= '{1}' AND timestamp::date < '{2}';".format(result_log_partition_table, partition_date,end_date)
        db.session.execute(sql)
        constraint_sql="alter table {0} alter column id set not null," \
                        "alter column name set not null,alter column node_id set not null;".format(result_log_partition_table)
        db.session.execute(constraint_sql)
        set_created_at="update {0} set created_at=timestamp;".format(result_log_partition_table)
        db.session.execute(set_created_at)
        set_query_name= "update {0} set name='windows_real_time_events' where name='windows_events';".format(result_log_partition_table)
        db.session.execute(set_query_name)
        attach_sql="alter table result_log attach partition {0} for values from ('{1}') to ('{2}');".format(result_log_partition_table, partition_date, end_date)
        db.session.execute(attach_sql)
        update_node_query_count = "INSERT INTO node_query_count(total_results,node_id,query_name,event_id,date)" \
                                    " SELECT count(*),node_id,name,columns->>'eventid',created_at::date " \
                                    "FROM {0} group by name,node_id,columns->>'eventid',created_at::date;".format(result_log_partition_table)

        db.session.execute(update_node_query_count)
        db.session.commit()
        create_index_and_trigger(result_log_partition_table,node_query_count_partition_table)
        add_result_log_map_data(result_log_partition_table)
        end_time = dt.datetime.utcnow()
        print('Added parttion - {} in {}'.format(result_log_partition_table,end_time-start_time))
        current_app.logger.debug('Added partition for {}'.format(result_log_partition_table))
    except Exception as e:
        db.session.rollback()
        current_app.logger.debug(e)
        print(e)



@manager.command
def drop_old_data():
    db.session.execute('drop table result_log_old;')
    db.session.execute('drop table node_query_count_old;')
    db.session.commit()


from polylogyx.utils.log_setting import _set_log_level_to_db,_check_log_level_exists
@manager.option("--log_level", default="WARNING")
def set_log_level(log_level):
    if not _check_log_level_exists():
        _set_log_level_to_db(log_level)

if __name__ == '__main__':
    manager.run()
