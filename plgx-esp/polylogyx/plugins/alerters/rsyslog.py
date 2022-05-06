# -*- coding: utf-8 -*-
import json
import logging
import socket
import os

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

    def handle_alert(self, node, match, intel_match):
        import datetime as dt

        self.incident_count += 1
        key = self.key_format.format(count=self.incident_count)

        if match:
            current_app.logger.log(logging.WARNING, "Triggered alert: {0!r}".format(match))
            description = match.rule.template.safe_substitute(match.result["columns"], **node).rstrip()

            description = ":".join(description.split("\r\n\r\n", 1))

            payload = json.dumps(
                append_node_and_rule_information_to_alert(
                    node,
                    flatten_json(
                        {
                            "event_type": "trigger",
                            "service_key": self.service_key,
                            "incident_key": key,
                            "description": description,
                            "host_identifier": node["host_identifier"],
                            "client": "PolyLogyx",
                            "client_url": self.client_url,
                            "query_name": match.result["name"],
                            "rule_name": match.rule.name,
                            "rule_description": match.rule.description,
                            "rule_status": match.rule.status,
                            "severity": match.rule.severity,
                            "alert_type": "Rule",
                            "created_at": dt.datetime.utcnow(),
                            "action": match.result["action"],
                            "columns": match.result["columns"],
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
                            "event_type": "trigger",
                            "service_key": self.service_key,
                            "incident_key": key,
                            "host_identifier": node["host_identifier"],
                            "client": "PolyLogyx",
                            "client_url": self.client_url,
                            "alert_type": "Threat Intel",
                            "query_name": intel_match.intel["query_name"],
                            "source_data": intel_match.data,
                            "source": intel_match.intel["source"],
                            "severity": intel_match.intel["severity"],
                            "created_at": dt.datetime.utcnow(),
                            "columns": intel_match.result,
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
