# -*- coding: utf-8 -*-
import json

from flask import current_app
from sqlalchemy import func

from polylogyx.db.database import db
from polylogyx.db.models import Node, ResultLog, ResultLogScan
from polylogyx.plugins import AbstractAlerterPlugin


def check_and_save_intel_alert(scan_id, scan_type, scan_value, data, source, severity):
    from polylogyx.db.models import Alerts, db

    # result_logs = ResultLog.query.filter(ResultLog.columns[scan_type].astext == scan_value).all()
    result_logs = ResultLog.query.filter(ResultLog.result_log_scans.any(ResultLogScan.id == scan_id)).all()
    for result_log in result_logs:
        alert_count = (
            db.session.query(func.count(Alerts.id))
            .filter(Alerts.source == source)
            .filter(Alerts.result_log_uid == result_log.uuid)
            .scalar()
        )
        if alert_count == 0:
            save_intel_alert(
                data=data,
                source=source,
                severity=severity,
                query_name=result_log.name,
                uuid=result_log.uuid,
                columns=result_log.columns,
                node_id=result_log.node,
            )


def send_alert(node, rule_match, intel_match):
    from polylogyx.db.models import current_app as app
    from polylogyx.utils.cache import get_a_host,get_host_dict
    node= get_host_dict(node)
    alerters = app.config.get("POLYLOGYX_ALERTER_PLUGINS", {})
    for name, (plugin, config) in alerters.items():
        package, classname = plugin.rsplit(".", 1)
        from importlib import import_module

        module = import_module(package)
        klass = getattr(module, classname, None)

        if klass is None:
            raise ValueError('Could not find a class named "{0}" in package "{1}"'.format(classname, package))

        if not issubclass(klass, AbstractAlerterPlugin):
            raise ValueError("{0} is not a subclass of AbstractAlerterPlugin".format(name))
        alerters[name] = klass(config)
    for alerter in alerters:
        try:
            alerters[alerter].handle_alert(node, rule_match, intel_match)
        except Exception as e:
            current_app.logger.error(e)



def save_intel_alert(data, source, severity, query_name, uuid, columns, node_id):
    from polylogyx.db.models import Alerts

    alert = Alerts.create(
        message=columns,
        query_name=query_name,
        result_log_uid=uuid,
        node_id=node_id.id,
        rule_id=None,
        type=Alerts.THREAT_INTEL,
        source=source,
        source_data=data,
        severity=severity,
    )
    from polylogyx.utils.rules import IntelMatch

    intel = {"type": Alerts.THREAT_INTEL, "source": source, "severity": severity, "query_name": query_name}
    json_data = ""
    if data:
        json_data = json.dumps(data)
    # This should be rechecked as its passing node id to node thing
    intel_match = IntelMatch(intel=intel, result=columns, data=json_data, alert_id=alert.id, node=node_id.id)
    try:
        send_alert(node_id, None, intel_match)
    except Exception as e:
        current_app.logger.error(e)


def save_intel_alert_new(ioc_alerts,node):
    from polylogyx.db.models import Alerts,db 
    db.session.bulk_save_objects(ioc_alerts,return_defaults=True)
    db.session.commit()
    
    from polylogyx.utils.rules import IntelMatch
    for alert in ioc_alerts:
        intel = {"type": Alerts.THREAT_INTEL, "source": alert.source, "severity": alert.severity, "query_name": alert.query_name}
        json_data = ""
        if alert.source_data:
            json_data = json.dumps(alert.source_data)
        # This should be rechecked as its passing node id to node thing
        intel_match = IntelMatch(intel=intel, result=alert.message, data=json_data, alert_id=alert.id, node=node.id)
        try:
            send_alert(node, None, intel_match)
        except Exception as e:
            current_app.logger.error(e)
