#!/usr/bin/env python
# set async_mode to 'threading', 'eventlet', 'gevent' or 'gevent_uwsgi' to
# force a mode else, the best mode is selected automatically from what's
# installed
# -*- coding: utf-8 -*-
import glob
import ssl
from os.path import abspath, dirname, join
import click

from flask import current_app, request, g
from flask_sockets import Sockets, Rule

from polylogyx import create_app, db
from polylogyx.models import ThreatIntelCredentials
from polylogyx.settings import  RabbitConfig
from polylogyx.settings import CurrentConfig, DevConfig, TestConfig
import json
import socketio
import functools
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


@click.argument('remaining', required=False)
@app.cli.command("test", help="Runs unit testcases")
def test(remaining=[]):
    test_cls = Test()
    if remaining:
        remaining = [remaining]
    test_cls.run(remaining)


class Test():
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


@app.cli.command('add_existing_yara_filenames_to_json',help="mapping old yara files to json")
def add_existing_yara_filenames_to_json():
    import os
    from os import walk
    file_list = []
    data = {}
    for (dirpath, dirnames, filenames) in walk(current_app.config['BASE_URL'] + "/yara/"):
        file_list.extend(filenames)
        break
    if len(file_list)==0:
        with open(os.path.join(current_app.config['BASE_URL'], 'yara', 'list.txt'), 'w') as the_file:
            pass
    files = [file_name + '\n' for file_name in file_list if file_name != 'list.txt' and file_name != 'list.json']
    jsonfile = os.path.join(current_app.config['BASE_URL'], 'yara', 'list.json')
    if not os.path.isfile(jsonfile) :
        for platform  in ['windows','linux']:
            data[platform] = []
            data[platform].extend(files)
        with open(os.path.join(current_app.config['BASE_URL'], 'yara', 'list.json'), 'w') as jsonfile:
            json.dump(data, jsonfile)


@sockets.route('/distributed/result',websocket=True)
def distributed_result(ws):
    """
    Web socket URL to fetch the results of live queries published from ESP container
    """
    message = str(ws.receive())
    try:
        ws.send('Fetching results for query with query id: {}'.format(message))
        consumer = Consumer("live_query", message, ws)
        consumer.run()
    except Exception as e:
        print(str(e))


@sockets.route('/csv/export',websocket=True)
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
            # If not acknowledged from response action section listed above, it has to be acknowledged
            cb = functools.partial(self.ack_message, delivery_tag, status)
            self.connection.add_callback_threadsafe(cb)

    def push_results_to_web_socket(self, body):
        """Pushes the results to the web socket end, connected to fetch results of LiveQuery"""
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


def set_log_level(log_level):
    from polylogyx.log_setting import get_log_level_setting, update_log_level_setting
    if not get_log_level_setting():
        update_log_level_setting(log_level)


@click.option("--log_level", default="WARNING", help="Log level that application server uses to log")
@app.cli.command('set_log_level', help="Updates the er server log level")
def set_log_level_command(log_level):
    set_log_level(log_level)


sockets.url_map.add(Rule('/distributed/result', endpoint=distributed_result, websocket=True))
sockets.url_map.add(Rule('/csv/export', endpoint=csv_export, websocket=True))

@app.cli.command('show_urls', help="lists all urls")
def list_routes():
    import urllib
    output = []
    for rule in app.url_map.iter_rules():
        methods = ','.join(rule.methods)
        line = urllib.parse.unquote("{:50s} {:50s} {}".format(rule.endpoint, methods, rule))
        output.append(line)
    for line in sorted(output):
        print(line)


if __name__ == '__main__':
    if CurrentConfig == DevConfig:
        ssl_context = ('../nginx/certificate.crt', '../nginx/private.key')
        app.run(debug=True, use_debugger=True, use_reloader=False, passthrough_errors=True,
                host='0.0.0.0', port=5001,
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
