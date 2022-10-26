# -*- coding: utf-8 -*-
import datetime as dt
import string

from flask import current_app, render_template

from polylogyx.db.models import AlertEmail

from .base import AbstractAlerterPlugin


class EmailAlerter(AbstractAlerterPlugin):
    def __init__(self, config):
        self.config = config

    def handle_alert(self, node, match=None, intel_match=None):
        if match:
            alert_id = match.alert_id
        elif intel_match:
            alert_id = intel_match.alert_id
        else:
            alert_id = None
        alert_email = AlertEmail.query.filter(AlertEmail.alert_id == alert_id).first()
        if not alert_email:
            params = {}
            params.update(node)
            params.update(node.get("node_info", {}))
            server_url = self.set_server_name()
            message_template = self.config.setdefault(
                'message_template', 'email/alert.body.txt'
            )

            if match:
                params.update(match.result["columns"])
            elif intel_match:
                message_template = "email/intel_alert.body.txt"
                params.update(intel_match.result)
            server_url = server_url.replace("9000", "443")

            body = string.Template(
                render_template(
                    message_template,
                    match=match,
                    intel_match=intel_match,
                    timestamp=dt.datetime.utcnow(),
                    node=node,
                    server_url=server_url,
                )
            ).safe_substitute(**params)

            email_alert = AlertEmail(node_id=node["id"], alert_id=alert_id, body=body)
            email_alert.save(email_alert)
        return

    def set_server_name(self):
        import os
        """
        Check server platform and then try to make file path dynamic
        """
        SERVER_URL = "localhost:9000"
        # flag_file_path = os.path.abspath('.') + "/resources/linux/x64/osquery.flags"
        flag_file_path = os.path.join(current_app.config.get('RESOURCES_URL', ''), 'linux', 'x64', 'osquery.flags')
        try:
            with open(flag_file_path, "r") as fi:
                for ln in fi:
                    if ln.startswith("--tls_hostname="):
                        SERVER_URL = (ln[len("--tls_hostname=") :]).replace("\r", "").replace("\n", "")
        except Exception as e:
            print(str(e))
        return SERVER_URL
