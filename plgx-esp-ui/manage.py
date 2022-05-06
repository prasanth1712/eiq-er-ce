#!/usr/bin/env python
# set async_mode to 'threading', 'eventlet', 'gevent' or 'gevent_uwsgi' to
# force a mode else, the best mode is selected automatically from what's
# installed
# -*- coding: utf-8 -*-
import ast
import glob
import ssl
import time
import datetime as dt
from os.path import abspath, dirname, join

import pika

from flask import current_app, request
from flask_migrate import MigrateCommand
from flask_script import Command, Manager, Server, Shell
from flask_script.commands import Clean, ShowUrls
from flask_sockets import Sockets

from polylogyx import create_app, db
from polylogyx.models import ThreatIntelCredentials
from polylogyx.settings import CurrentConfig, RabbitConfig
import json
import socketio
import datetime as dt
import functools
import logging
import threading
import time
import pika

from polylogyx.utils import validate_osquery_query


app = create_app(config=CurrentConfig)


async_mode = 'gevent'
sio = socketio.Server(logger=True, async_mode=async_mode)
sockets = Sockets(app)
app.wsgi_app = socketio.Middleware(sio, app.wsgi_app)


with app.app_context():
    validate_osquery_query('select * from processes;')


def _make_context():
    return {'app': app, 'db': db}


class SSLServer(Command):
    """
    Run WSGI server with SSL context
    """
    def run_server(self):
        from gevent import pywsgi
        from werkzeug.debug import DebuggedApplication
        from geventwebsocket.handler import WebSocketHandler

        validate_osquery_query('select * from processes;')
        pywsgi.WSGIServer(('', 5000), DebuggedApplication(app),
                          handler_class=WebSocketHandler,
                          keyfile='../nginx/private.key', certfile='../nginx/certificate.crt'
                          ).serve_forever()

    def run(self, *args, **kwargs):
        if __name__ == '__main__':
            from werkzeug.serving import run_with_reloader
            run_with_reloader(self.run_server())


manager = Manager(app)
manager.add_command('server', Server())

manager.add_command('shell', Shell(make_context=_make_context))
manager.add_command('db', MigrateCommand)
manager.add_command('clean', Clean())
manager.add_command('urls', ShowUrls())
manager.add_command('ssl', SSLServer())


@manager.add_command
class test(Command):
    name = 'test'
    capture_all_args = True

    def run(self, remaining):
        import pytest
        test_path = join(abspath(dirname(__file__)), 'tests')

        if remaining:
            test_args = remaining + ['--verbose']
        else:
            test_args = [test_path, '--verbose']

        exit_code = pytest.main(test_args)
        return exit_code


@manager.command
def add_existing_yara_filenames_to_json():
    import os
    from os import walk
    file_list = []
    data = {}
    for (dirpath, dirnames, filenames) in walk(current_app.config['BASE_URL'] + "/yara/"):
        file_list.extend(filenames)
        break
    files = [file_name + '\n' for file_name in file_list if file_name != 'list.txt' and file_name != 'list.json']
    jsonfile = os.path.join(current_app.config['BASE_URL'], 'yara', 'list.json')
    if not os.path.isfile(jsonfile) :
        for platform  in ['windows','linux']:
            data[platform] = []
            data[platform].extend(files)
        with open(os.path.join(current_app.config['BASE_URL'], 'yara', 'list.json'), 'w') as jsonfile:
            json.dump(data, jsonfile)


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
    from polylogyx.extract_ddl import extract_schema, extract_schema_json
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
            if table_dict['platform']:
                full_schema.append(table_dict)
        opath = join(dirname(__file__), 'polylogyx', 'resources', target_file)
        content = json.dumps(full_schema)
    else:
        print("Export type given is invalid!")
        opath = None
        content = None

    with open(opath, 'w') as f:
        if export_type == 'sql':
            f.write('-- This file is generated using "python manage.py extract_ddl"'
                    '- do not edit manually\n')
        f.write(content)
    current_app.logger.info('OSQuery Schema is exported to the file {} successfully'.format(opath))


@manager.option('--IBMxForceKey')
@manager.option('--IBMxForcePass')
@manager.option('--VT_API_KEY')
def add_api_key(IBMxForceKey, IBMxForcePass, VT_API_KEY):
    import os
    ibm_x_force_credentials = ThreatIntelCredentials.query.filter(ThreatIntelCredentials.intel_name == 'ibmxforce').first()

    vt_credentials = ThreatIntelCredentials.query.filter(ThreatIntelCredentials.intel_name == 'virustotal').first()
    if vt_credentials:
        current_app.logger.info('Virus Total Key already exists')
    else:
        credentials = {}
        credentials['key'] = VT_API_KEY
        ThreatIntelCredentials.create(intel_name='virustotal', credentials=credentials)
        current_app.logger.info("Added VirusTotal Key successfully!")
    OTX_API_KEY = os.environ.get('ALIENVAULT_OTX_KEY')
    if OTX_API_KEY:
        otx_credentials = ThreatIntelCredentials.query.filter(ThreatIntelCredentials.intel_name == 'alienvault').first()
        if otx_credentials:
            current_app.logger.info('AlienVault  Key already exists')
        else:
            credentials={}
            credentials['key'] = OTX_API_KEY
            ThreatIntelCredentials.create(intel_name='alienvault', credentials=credentials)
            current_app.logger.info("Added AlienVault Key successfully!")

    if ibm_x_force_credentials:
        current_app.logger.info('Ibm Key already exists')
    else:
        credentials={}
        credentials['key'] = IBMxForceKey
        credentials['pass'] = IBMxForcePass
        ThreatIntelCredentials.create(intel_name='ibmxforce', credentials=credentials)
        current_app.logger.info("Added IBMXForce Key successfully!")
    exit(0)


@sockets.route('/distributed/result')
def distributed_result(ws):
    """
    Web socket URL to fetch the results of live query results published from ESP container
    """
    message = str(ws.receive())
    try:
        ws.send('Fetching results for query with query id: {}'.format(message))
        consumer = Consumer("live_query", message, ws)
        consumer.run()
    except Exception as e:
        print(str(e))


@sockets.route('/csv/export')
def csv_export(ws):
    """
    Web socket URL to fetch the results of csv export published from  celery task
    """
    message = str(ws.receive())
    try:
        ws.send('Fetching results for task with id: {}'.format(message))
        consumer = Consumer("csv_export", message, ws)
        consumer.run()
    except Exception as e:
        print(str(e))


class Consumer:
    """Consumes the messages from rabbitmq exchange and closes the exchange and queue
            after the time interval(max_wait_time) set
    Pushes the actual query results to the web socket
    """
    def __init__(self, type, object_id, ws):
        self._is_interrupted = False
        self.object_id = object_id
        self.ws = ws
        self.type = type
        self.exchange_name = f"{self.type}_{self.object_id}"
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(
            host=current_app.config['RABBITMQ_HOST'], port=current_app.config['RABBITMQ_PORT'],
            credentials=current_app.config['RABBIT_CREDS'], ssl=current_app.config['RABBITMQ_USE_SSL'],
            ssl_options={"cert_reqs": ssl.CERT_NONE}, heartbeat=300, blocked_connection_timeout=300))
        self.channel = self.connection.channel()
        self.started_at = time.time()

    def close_connection(self):
        """
        Closes connection to RabbitMQ queue from Pika
        """
        self._is_interrupted = True
        self.channel.stop_consuming()
        self.channel.close()
        self.connection.close()

    def delete_queue(self):
        """
        Removes RabbitMQ queue and exchange as we are done with the queue and exchange(Mostly on 10min timeout)
        """
        self.channel.stop_consuming()
        self.channel.exchange_delete(self.exchange_name)
        self.channel.queue_delete(self.exchange_name)
        self.channel.close()
        self.connection.close()

    def run(self):
        try:
            for message in self.channel.consume(self.exchange_name, inactivity_timeout=RabbitConfig.inactivity_timeout):
                method, properties, body = message
                if method and body and time.time()-self.started_at < RabbitConfig.max_wait_time:
                    # To process the message only received within time and is not None
                    self.proc_message(method.delivery_tag, body)
                elif time.time()-self.started_at >= RabbitConfig.max_wait_time:
                    print(f"Reached 10 min timeout for '{self.exchange_name}', So killing the queue and consumer!")
                    self.delete_queue()  # RabbitMQ queue will be deleted when timeout hits
                    break
                elif self._is_interrupted:
                    print(f"Interrupted for '{self.exchange_name}'")
                    break
        except pika.exceptions.ChannelClosed as e:
            print("Pika queue/exchange closed - ", str(e))
            self.connection.close()  # Close connection if channel has been already closed
        except pika.exceptions.ConnectionClosed as e:
            print("Pika connection closed - ", str(e))
        self.ws.close()  # Close websocket connection on Consumer completion/Channel close/Connection close

    def ack_message(self, delivery_tag, status):
        """Note that `ch` must be the same pika channel instance via which
        the message being ACKed was retrieved (AMQP protocol constraint).
        """
        if self.channel.is_open:
            if not self.ws.closed and status:
                self.channel.basic_ack(delivery_tag)  # Message acknowledgement will be sent to RabbitMQ
            else:
                self.channel.basic_nack(delivery_tag)  # Message acknowledgement(negative) will be sent to RabbitMQ
                self.close_connection()  # Close connection if not able to emit to UI web socket
        else:
            # Channel is already closed, so we can't ACK this message;
            # log and/or do something that makes sense for your app in this case.
            pass

    def proc_message(self, delivery_tag, body):
        acknowledged = False
        status = self.push_results_to_web_socket(body)
        if not acknowledged:
            cb = functools.partial(self.ack_message, delivery_tag, status)
            self.connection.add_callback_threadsafe(cb)

    def push_results_to_web_socket(self, body):
        """Pushes the results to the web socket end, connected to fetch results of LiveQuery/ResponseAction"""
        if self.ws and not self.ws.closed:
            self.ws.send(body)
            return True
        else:
            print('Web socket connection closed')
        return False


def declare_queue(object_id, type='live_query'):
    """Creates exchange, queue(non-exclusive) and binds the the exchange to the queue"""
    exchange_name = "{}_{}".format(type, object_id)

    connection = pika.BlockingConnection(pika.ConnectionParameters(host=current_app.config['RABBITMQ_HOST'],
                                                                   port=current_app.config['RABBITMQ_PORT'],
                                                                   credentials=current_app.config['RABBIT_CREDS'],
                                                                   ssl=current_app.config['RABBITMQ_USE_SSL'],
                                                                   ssl_options={"cert_reqs": ssl.CERT_NONE}))
    channel = connection.channel()
    channel.exchange_declare(exchange=exchange_name, auto_delete=True)
    result = channel.queue_declare(queue=exchange_name, exclusive=False,
                                   arguments={'x-message-ttl': RabbitConfig.max_wait_time * 1000,
                                              'x-expires': RabbitConfig.max_wait_time * 1000})
    queue_name = result.method.queue
    channel.queue_bind(exchange=exchange_name, queue=queue_name)
    # Note: prefetch is set to 1 here as an example only and to keep the number of threads created
    # to a reasonable amount. In production, you will want to test with different prefetch values
    # to find which one provides the best performance and usability for your solution
    current_app.logger.info(f"A Queue and Exchange are declared with name: {queue_name}")


@app.before_request
def before_request_method():
    from polylogyx.cache import get_log_level
    from polylogyx.log_setting import set_app_log_level
    set_app_log_level(get_log_level())
    if request.method == 'POST' or request.method == 'PUT' and request.endpoint != 'external_api_v1.get_auth_token' \
            and request.endpoint != 'external_api.get_auth_token':
        current_app.logger.debug(
            "Requested endpoint '{0}' with URL '{1}' and with payload: \n{2}\n".format(
                request.endpoint, request.url, request.get_json()))
    else:
        current_app.logger.debug(
            "Requested endpoint '{0}' with URL '{1}'".format(request.endpoint, request.url))


@app.after_request
def add_response_headers(response):
    response.headers.add('Access-Control-Allow-Methods', 'PUT, GET, POST, DELETE, OPTIONS')
    # response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,x-access-token,content-type')
    response.headers.add('Access-Control-Expose-Headers', 'Content-Type,Content-Length,Authorization,X-Pagination')
    return response


from polylogyx.log_setting import _set_log_level_to_db,_check_log_level_exists


@manager.option("--log_level", default="WARNING")
def set_log_level(log_level):
    if not _check_log_level_exists():
        _set_log_level_to_db(log_level)


if __name__ == '__main__':
    manager.run()

