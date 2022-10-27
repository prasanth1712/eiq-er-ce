# -*- coding: utf-8 -*-
import json
import logging
import socket
import os
import string

from flask import current_app

from polylogyx.utils.generic import DateTimeEncoder, flatten_json
from polylogyx.utils.node import append_node_and_rule_information_to_alert

from .base import AbstractAlerterPlugin

DEFAULT_KEY_FORMAT = "polylogyx-incident-{count}"


class RsyslogAlerter(AbstractAlerterPlugin):
    def __init__(self, config):
        # Required configuration
        self.service_key = config["service_key"]

        # Optional
        self.client_url = config.get("client_url", "")
        self.key_format = config.get("key_format", DEFAULT_KEY_FORMAT)

        # Other
        self.incident_count = 0
        self.logger = logging.getLogger(__name__ + ".RsyslogAlerter")
        self.rsyslog_address = os.environ.get('RSYSLOG_ADDRESS', 'rsyslogf')
        self.rsyslog_port = int(os.environ.get('RSYSLOG_PORT', '514'))

    @staticmethod
    def template(match):
        return string.Template("{name}\r\n\r\n{description}".format(name=match.rule['name'], description=match.rule['description'] or ""))

    def handle_alert(self, node, match, intel_match):
        import datetime as dt

        self.incident_count += 1
        key = self.key_format.format(count=self.incident_count)

        if match:
            current_app.logger.log(logging.WARNING, "Triggered alert: {0!r}".format(match))
            description = self.template(match).safe_substitute(match.result["columns"], **node).rstrip()

            description = ":".join(description.split("\r\n\r\n", 1))

            payload = json.dumps(
                append_node_and_rule_information_to_alert(
                    node,
                    flatten_json(
                        {

                            '_version': 2,
                            '_event_type': 'alert',
                            '_host_identifier': node['host_identifier'],
                            "_query_name": match.result['name'],
                            '_rule_name': match.rule['name'],
                            '_rule_description': match.rule['description'],
                            '_severity': match.rule['severity'],
                            '_alert_type': 'Rule',
                            '_created': dt.datetime.utcnow(),
                            '_action': match.result['action'],
                            'columns': match.result['columns']


                        }
                    ),
                ),
                cls=DateTimeEncoder,
            )
        elif intel_match:
            current_app.logger.log(logging.WARNING, "Triggered alert: {0!r}".format(intel_match))
            payload = json.dumps(
                append_node_and_rule_information_to_alert(
                    node,
                    flatten_json(
                        {

                            '_version': 2,
                            '_event_type': 'trigger',
                            '_host_identifier': node['host_identifier'],
                            '_alert_type': 'Threat Intel',
                            "_query_name": intel_match.intel['query_name'],
                            '_source_data': intel_match.data,
                            '_source': intel_match.intel['source'],
                            '_severity': intel_match.intel['severity'],
                            '_created': dt.datetime.utcnow(),
                            'columns': intel_match.result,


                        }
                    ),
                ),
                cls=DateTimeEncoder,
            )

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((self.rsyslog_address, self.rsyslog_port))
            bSock = True
            current_app.logger.info("[alert] Socket connected")
        except:
            bSock = False
            current_app.logger.error(
                "Unable to socket connect, is rsyslog forwarder running? If not, disable rsyslog forwading in docker compose file."
            )

        try:
            if bSock:
                sock.send(payload.encode("utf-8"))
                sock.send("\n".encode("utf-8"))
        finally:
            if bSock:
                sock.close()
                current_app.logger.info("[alert] Socket closed")
