# -*- coding: utf-8 -*-
import datetime as dt
import ssl

import pika

import json, os, sqlite3, string, threading, pkg_resources, requests, base64
from collections import namedtuple
from functools import wraps

from operator import itemgetter
from os.path import join
from sqlalchemy import and_, or_, not_

from flask_mail import Message, Mail
from flask import current_app, flash, request, abort

from polylogyx.constants import PolyLogyxServerDefaults, DEFAULT_PLATFORMS
from polylogyx.database import db
from polylogyx.models import (
    DistributedQuery, DistributedQueryTask, HandlingToken,
    Node, Pack, Query, ResultLog, querypacks,
    Options, Settings, AlertEmail, Tag, User, DefaultFilters, DefaultQuery, Config, NodeConfig)


Field = namedtuple('Field', ['name', 'action', 'columns', 'timestamp'])

# Read DDL statements from our package
schema = pkg_resources.resource_string('polylogyx', join('resources', 'osquery_schema.sql'))
schema = schema.decode('utf-8')
schema = [x for x in schema.strip().split('\n') if not x.startswith('--')]

extension_schema = pkg_resources.resource_string('polylogyx', join('resources', 'extension_schema.sql'))
extension_schema = extension_schema.decode('utf-8')
extension_schema = [x for x in extension_schema.strip().split('\n') if not x.startswith('--')]

# SQLite in Python will complain if you try to use it from multiple threads.
# We create a threadlocal variable that contains the DB, lazily initialized.
osquery_mock_db = threading.local()


def send_test_mail(settings):
    from flask import Flask
    test_app = Flask(__name__)
    test_app.config['EMAIL_RECIPIENTS'] = settings['emailRecipients']
    test_app.config['MAIL_USERNAME'] = settings['email']
    test_app.config['MAIL_PASSWORD'] = settings['password']
    test_app.config['MAIL_SERVER'] = settings['smtpAddress']
    test_app.config['MAIL_PORT'] = int(settings.get('smtpPort', 465))
    test_app.config['MAIL_USE_SSL'] = settings['use_ssl']
    test_app.config['MAIL_USE_TLS'] = settings['use_tls']

    content = """Test message"""
    subject = "Sent from EclecticIQ Endpoint Response"
    return send_mail(test_app, content, subject)


def send_mail(app, content, subject):
    import socket
    socket.setdefaulttimeout(30)
    if app.config['EMAIL_RECIPIENTS']:
        message = Message(
            subject.strip(),
            sender=app.config['MAIL_USERNAME'],
            recipients=app.config['EMAIL_RECIPIENTS'],
            body=content,
            charset='utf-8',
        )
        mail = Mail(app=app)
        try:
            mail.send(message)
            return True
        except Exception as e:
            current_app.logger.error("Unable to send mail - {}".format(str(e)))
    return False


def assemble_additional_configuration(node):
    configuration = {}
    configuration['queries'] = assemble_queries(node)
    configuration['packs'] = assemble_packs(node)
    configuration['tags'] = [tag.value for tag in node.tags]
    return configuration


def assemble_configuration(node):
    from polylogyx.dao.v1 import configs_dao
    config = configs_dao.get_config_of_node(node)
    configuration = assemble_filters(config)
    configuration['options'] = assemble_options(node, configuration)
    configuration['schedule'] = assemble_schedule(node, config)
    configuration['packs'] = assemble_packs(node)
    if config:
        config_details = {'id': config.id, 'name': config.name}
    else:
        config_details = {}
    return configuration, config_details


def assemble_options(node, configuration):
    options = {'disable_watchdog': True, 'logger_tls_compress': True}

    # https://github.com/facebook/osquery/issues/2048#issuecomment-219200524
    if current_app.config['POLYLOGYX_EXPECTS_UNIQUE_HOST_ID']:
        options['host_identifier'] = 'uuid'
    else:
        options['host_identifier'] = 'hostname'

    options['schedule_splay_percent'] = 10
    existing_option = Options.query.filter(Options.name == PolyLogyxServerDefaults.plgx_config_all_options).first()
    if existing_option:
        existing_option_value = json.loads(existing_option.option)
        options = merge_two_dicts(options, existing_option_value)
    options.update(configuration.get('options', {}))
    return options


def assemble_queries(node, config_json=None):
    if config_json:
        schedule = {}
        for query in node.queries.options(db.lazyload('*')):
            schedule[query.name] = query.to_dict()
        if config_json:
            schedule = merge_two_dicts(schedule, config_json.get('schedule'))
    else:
        schedule = []
        for query in node.queries.options(db.lazyload('*')):
            schedule.append(query.to_dict())
    return schedule


def assemble_schedule(node, config=None):
    schedule = {}
    for query in node.queries.options(db.lazyload('*')):
        schedule[query.name] = query.to_dict()
    queries = db.session.query(DefaultQuery).filter(
        DefaultQuery.config == config).filter(DefaultQuery.status).all()

    for default_query in queries:
        schedule[default_query.name] = default_query.to_dict()

    return schedule


def assemble_packs(node, config_json=None):
    if config_json:
        packs = {}
        for pack in node.packs.join(querypacks).join(Query) \
                .options(db.contains_eager(Pack.queries)).all():
            packs[pack.name] = pack.to_dict()
        if config_json:
            packs = merge_two_dicts(packs, config_json.get('packs'))
    else:
        packs = []
        for pack in node.packs.join(querypacks).join(Query) \
                .options(db.contains_eager(Pack.queries)).all():
            packs.append(pack.to_dict())
    return packs


def assemble_distributed_queries(node):
    """
    Retrieve all distributed queries assigned to a particular node
    in the NEW state. This function will change the state of the
    distributed query to PENDING, however will not commit the change.
    It is the responsibility of the caller to commit or rollback on the
    current database session.
    """
    now = dt.datetime.utcnow()
    pending_query_count = 0
    query_recon_count = db.session.query(db.func.count(DistributedQueryTask.id)) \
        .filter(
        DistributedQueryTask.node == node,
        DistributedQueryTask.status == DistributedQueryTask.NEW,
        DistributedQueryTask.priority == DistributedQueryTask.HIGH,

    )
    for r in query_recon_count:
        pending_query_count = r[0]
    if pending_query_count > 0:
        query = db.session.query(DistributedQueryTask) \
            .join(DistributedQuery) \
            .filter(
            DistributedQueryTask.node == node,
            DistributedQueryTask.status == DistributedQueryTask.NEW,
            DistributedQuery.not_before < now,
            DistributedQueryTask.priority == DistributedQueryTask.HIGH,

        ).options(
            db.lazyload('*'),
            db.contains_eager(DistributedQueryTask.distributed_query)
        )
    else:
        query = db.session.query(DistributedQueryTask) \
            .join(DistributedQuery) \
            .filter(
            DistributedQueryTask.node == node,
            DistributedQueryTask.status == DistributedQueryTask.NEW,
            DistributedQuery.not_before < now,
            DistributedQueryTask.priority == DistributedQueryTask.LOW,
        ).options(
            db.lazyload('*'),
            db.contains_eager(DistributedQueryTask.distributed_query)
        ).limit(1)

    queries = {}
    for task in query:
        if task.sql:
            queries[task.guid] = task.sql
        else:
            queries[task.guid] = task.distributed_query.sql
        task.update(status=DistributedQueryTask.PENDING,
                    timestamp=now,
                    commit=False)

        # add this query to the session, but don't commit until we're
        # as sure as we possibly can be that it's been received by the
        # osqueryd client. unfortunately, there are no guarantees though.
        db.session.add(task)
    return queries


def assemble_filters(config):
    default_filters_obj = DefaultFilters.query.filter(DefaultFilters.config == config).first()
    if default_filters_obj:
        return default_filters_obj.filters
    else:
        return {}


def create_tags(*tags):
    values = []
    existing = []

    # create a set, because we haven't yet done our association_proxy in
    # sqlalchemy

    for value in (v.strip() for v in set(tags) if v.strip()):
        tag = Tag.query.filter(Tag.value == value).first()
        if not tag:
            values.append(Tag.create(value=value))
        else:
            existing.append(tag)
    else:
        if values:
            flash(u"Created tag{0} {1}".format(
                's' if len(values) > 1 else '',
                ', '.join(tag.value for tag in values)),
                'info')
    return values + existing


def get_tags(*tags):
    values = []
    existing = []

    # create a set, because we haven't yet done our association_proxy in
    # sqlalchemy

    for value in (v.strip() for v in set(tags) if v.strip()):
        tag = Tag.query.filter(Tag.value == value).first()
        if tag:
            existing.append(tag)
    return existing


def merge_two_dicts(x, y):
    if not x:
        x = {}
    if not y:
        y = {}
    z = x.copy()  # start with x's keys and values
    z.update(y)  # modifies z with y's keys and values & returns None
    return z


def create_mock_db():
    from polylogyx.extra_sql_methods import _carve, _split, _concat, _concat_ws, _regex_split, _regex_match, \
        _inet_aton, _community_id_v1, _to_base64, _from_base64, _conditional_to_base64, _sqrt, _log, _log10, _ceil, \
        _floor, _power, _sin, _cos, _cot, _tan, _asin, _acos, _atan, _degrees, _radians, _pi
    from polylogyx.constants import PolyLogyxServerDefaults

    mock_db = sqlite3.connect(':memory:')
    mock_db.create_function("carve", 1, _carve)
    mock_db.create_function("SPLIT", 3, _split)
    mock_db.create_function("concat", -1, _concat)
    mock_db.create_function("concat_ws", -1, _concat_ws)
    mock_db.create_function("regex_split", 3, _regex_split)
    mock_db.create_function("regex_match", 3, _regex_match)
    mock_db.create_function("inet_aton", 1, _inet_aton)
    mock_db.create_function("community_id_v1", -1, _community_id_v1)
    mock_db.create_function("to_base64", 1, _to_base64)
    mock_db.create_function("from_base64", 1, _from_base64)
    mock_db.create_function("conditional_to_base64", 1, _conditional_to_base64)
    mock_db.create_function("sqrt", 1, _sqrt)
    mock_db.create_function("log", 1, _log)
    mock_db.create_function("log10", 1, _log10)
    mock_db.create_function("ceil", 1, _ceil)
    mock_db.create_function("floor", 1, _floor)
    mock_db.create_function("power", 1, _power)
    mock_db.create_function("sin", 1, _sin)
    mock_db.create_function("cos", 1, _cos)
    mock_db.create_function("tan", 1, _tan)
    mock_db.create_function("asin", 1, _asin)
    mock_db.create_function("acos", 1, _acos)
    mock_db.create_function("atan", 1, _atan)
    mock_db.create_function("cot", 1, _cot)
    mock_db.create_function("degrees", 1, _degrees)
    mock_db.create_function("radians", 1, _radians)

    for ddl in schema:
        mock_db.execute(ddl)
    for ddl in extension_schema:
        mock_db.execute(ddl)
    cursor = mock_db.cursor()
    cursor.execute("SELECT name,sql FROM sqlite_master WHERE type='table';")
    for osquery_table in cursor.fetchall():
        PolyLogyxServerDefaults.POLYLOGYX_OSQUERY_SCHEMA_JSON[osquery_table[0]] = osquery_table[1]
    return mock_db


def validate_osquery_query(query):
    # Check if this thread has an instance of the SQLite database
    db = getattr(osquery_mock_db, 'db', None)
    if db is None:
        db = create_mock_db()
        osquery_mock_db.db = db
    try:
        db.execute(query)
    except sqlite3.Error:
        current_app.logger.info("Invalid query: %s", query)
        return False
    except sqlite3.Warning:
        current_app.logger.info("Invalid query: %s Only one query can be executed a time!", query)
        return False
    except sqlite3.OperationalError:
        current_app.logger.info("Invalid query: %s", query)
        return False
    return True


def is_token_logged_out(loggedin_token):
    qs_object = HandlingToken.query.filter(HandlingToken.token == loggedin_token).first()
    if qs_object and qs_object.token_expired:
        return True
    elif qs_object:
        return False
    return


def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from flask import g
        current_user_logged_in = User.verify_auth_token(request.headers.environ.get('HTTP_X_ACCESS_TOKEN'))
        if current_user_logged_in and current_user_logged_in.status is not False and \
                is_token_logged_out(request.headers.environ.get('HTTP_X_ACCESS_TOKEN')) is False:
            g.user = current_user_logged_in
            return f(*args, **kwargs)
        elif request.path.endswith('swagger.json'):
            return f(*args, **kwargs)
        elif User.is_auth_token_exists(request.headers.environ.get('HTTP_X_ACCESS_TOKEN')) or is_token_logged_out(request.headers.environ.get('HTTP_X_ACCESS_TOKEN')):
            return abort(401, {'message': 'This API key used to authenticate is expired!'})
        else:
            current_app.logger.error("%s - Request did not contain valid API key", request.remote_addr)
            return abort(401, {'message': 'Request did not contain valid API key!'})

    return decorated_function


def is_number_positive(number=None):
    if number > 0:
        return True
    else:
        return False


def push_results_to_queue(results, object_id, exchange):
    import pika
    connection = pika.BlockingConnection(pika.ConnectionParameters(
        host=current_app.config['RABBITMQ_HOST'], port=current_app.config['RABBITMQ_PORT'],
        credentials=current_app.config['RABBIT_CREDS'], ssl=current_app.config['RABBITMQ_USE_SSL'],
        ssl_options={"cert_reqs": ssl.CERT_NONE}))
    channel = connection.channel()
    channel.confirm_delivery()   # confirms True/False about the message delivery
    exchange_string = exchange + str(object_id)
    print(results)
    try:
        if channel.basic_publish(exchange=exchange_string, routing_key=exchange_string, body=json.dumps(results)):
            current_app.logger.info("Results for id {} were published successfully".format(object_id))
        else:
            current_app.logger.info("Failure in publishing  Results for task id {}".format(object_id))
    except Exception as e:
        current_app.logger.error(e)
    connection.close()


def get_server_ip():
    import os
    server_ip = "localhost"
    try:
        file_path = os.path.abspath('.') + "/resources/linux/x64/osquery.flags"
        with open(file_path, "r") as fi:
            for ln in fi:
                if ln.startswith("--tls_hostname="):
                    SERVER_URL = (ln[len('--tls_hostname='):]).replace('\r', '').replace('\n', '').split(':')
                    server_ip = SERVER_URL[0]
    except Exception as e:
        print("Unable to detect IP from the flags file -- {}".format(str(e)))
    return server_ip


def form_status_log_csv(results, node_id):
    import csv
    file_name = 'status_log_' + str(node_id) + '_' + str(dt.datetime.now()).replace(' ', '_') + '.csv'
    file_path = current_app.config['BASE_URL'] + "/status_log/" + file_name

    if results:
        try:
            results = [r for r in results]
            headers = []
            if not len(results) == 0:
                first_record = results[0]
                for key in first_record.keys():
                    headers.append(str(key))
            with open(file_path, mode='w') as csv_file:
                writer = csv.DictWriter(csv_file, fieldnames=headers)
                writer.writeheader()
                for data in results:
                    writer.writerow(data)
            download_path = 'https://{0}/downloads/status_log/{1}'.format(get_server_ip(), file_name)

            response = {
                'status': 'success',
                "message": "please fetch csv file from  download path",
                "download_path": download_path
            }
        except Exception as e:
            print(e)
            response = {
                'status': 'Failure',
                "message": "Something went wrong,Please try again"
            }
    else:
        response = {
            'status': 'Failure',
            "message": "No data found"
        }

    return response


def check_for_rabbitmq_status():
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=current_app.config['RABBITMQ_HOST'],
                                                                       port=current_app.config['RABBITMQ_PORT'],
                                                                       credentials=current_app.config['RABBIT_CREDS'],
                                                                       ssl=current_app.config['RABBITMQ_USE_SSL'],
                                                                       ssl_options={"cert_reqs": ssl.CERT_NONE}))
        connection.close()
        return True
    except Exception as error:
        current_app.logger.error(str(error))
        return False


def get_server_log_level():
    url = current_app.config['ESP_SERVER_ADDRESS'] + '/log_setting'
    requests.packages.urllib3.disable_warnings()
    response = requests.get(url, verify=False, timeout=10)
    return response.json()["log_level"]


def set_server_log_level(level):
    url = current_app.config['ESP_SERVER_ADDRESS'] + '/log_setting'
    requests.packages.urllib3.disable_warnings()
    response = requests.put(url, data=json.dumps({"log_level":level}), verify=False, timeout=10,
                                    headers={"content-type": "application/json"})
    return response.json()["log_level"]


def is_password_strong(password):
    if len(password) < 8 or password.lower() == password or password.upper() == password or password.isalnum() \
            or not any(i.isdigit() for i in password):
        return False
    return True
