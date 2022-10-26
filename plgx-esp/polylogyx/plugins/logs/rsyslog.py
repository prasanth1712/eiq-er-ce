# -*- coding: utf-8 -*-
import datetime as dt
import json
import socket
import os

from flask import current_app

from polylogyx.plugins import AbstractLogsPlugin
from polylogyx.utils.generic import DateTimeEncoder, flatten_json
from polylogyx.utils.js import quote
from polylogyx.utils.node import append_node_information_to_result_log


class RsyslogPlugin(AbstractLogsPlugin):
    def __init__(self, config):
        self.minimum_severity = config.get("POLYLOGYX_MINIMUM_OSQUERY_LOG_LEVEL")
        self.rsyslog_address = os.environ.get('RSYSLOG_ADDRESS', 'rsyslogf')
        self.rsyslog_port = int(os.environ.get('RSYSLOG_PORT', '514'))

    @property
    def name(self):
        return "json"

    def handle_status(self, data, **kwargs):
        minimum_severity = self.minimum_severity
        host_identifier = kwargs.get("host_identifier")
        created = dt.datetime.utcnow().isoformat()

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            sock.connect((self.rsyslog_address, self.rsyslog_port))
            bSock = True
            current_app.logger.info("[log] Socket connected")
        except:
            bSock = False
            current_app.logger.warning(
                "[log] Unable to socket connect, is rsyslog forwarder running? If not, disable rsyslog forwading in docker compose file."
            )

        try:
            for item in data.get("data", []):
                if int(item["severity"]) < minimum_severity:
                    continue

                if "created" in item:
                    item["created"] = item["created"].isoformat()

                # if bSock:
                #     sock.send(json.dumps({
                #         '@version': 1,
                #         '@host_identifier': host_identifier,
                #         '@timestamp': item.get('created', created),
                #         '@message': item.get('message', ''),
                #         'log_type': 'status',
                #         'line': item.get('line', ''),
                #         'message': item.get('message', ''),
                #         'severity': item.get('severity', ''),
                #         'filename': item.get('filename', ''),
                #         'osquery_version': item.get('version'),  # be null
                #         'created': created,
                #         }).encode('utf-8'))
                #
                #     sock.send('\n'.encode('utf-8'))
        finally:
            if bSock:
                sock.close()
                current_app.logger.info("[log] Socket closed")

    def handle_result(self, data, **kwargs):
        host_identifier = kwargs.get("host_identifier")
        created = dt.datetime.utcnow().isoformat()

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((self.rsyslog_address, self.rsyslog_port))
            bSock = True
            current_app.logger.info("[log] Socket connected")
        except:
            bSock = False
            current_app.logger.warning(
                "Unable to socket connect, is rsyslog forwarder running? If not, disable rsyslog forwading in docker compose file."
            )

        try:
            for item in data:
                if bSock:

                    sock.send(
                        json.dumps(
                            append_node_information_to_result_log(
                                kwargs.get("node"),
                                flatten_json(
                                    {
                                        '_version': 2,
                                        '_host_identifier': host_identifier,
                                        '_timestamp': item['timestamp'].isoformat(),
                                        '_event_type': 'log',
                                        '_log_type': 'result',
                                        '_action': item['action'],
                                        'columns': item['columns'],
                                        '_query_name': item['name'],
                                        '_created': created,
                                    }
                                ),
                            ),
                            cls=DateTimeEncoder,
                        ).encode("utf-8")
                    )

                    sock.send("\n".encode("utf-8"))
        finally:
            if bSock:
                sock.close()
                current_app.logger.info("[log] Socket closed")

    def handle_recon(self, data, **kwargs):
        host_identifier = kwargs.get("host_identifier")
        created = dt.datetime.utcnow().isoformat()

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((self.rsyslog_address, self.rsyslog_port))
            bSock = True
            current_app.logger.info("[log] Socket connected")
        except:
            bSock = False
            current_app.logger.warning(
                "Unable to socket connect, is rsyslog forwarder running? If not, disable rsyslog forwading in docker compose file."
            )

        try:

            if bSock:
                sock.send(
                    json.dumps(
                        flatten_json(
                            {
                                "@version": 1,
                                "hostIdentifier": host_identifier,
                                "log_type": "recon",
                                "columns": data,
                                "query_name": kwargs.get("name"),
                                "created": created,
                            }
                        )
                    ).encode("utf-8")
                )

                sock.send("\n".encode("utf-8"))
        finally:
            if bSock:
                sock.close()
                current_app.logger.info("[log] Socket closed")
