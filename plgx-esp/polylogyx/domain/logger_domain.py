import datetime as dt
import json

from flask import current_app

from polylogyx.celery.tasks import save_and_analyze_results
from polylogyx.db.database import db
from polylogyx.db.models import ResultLog, StatusLog
from polylogyx.extensions import log_tee


class LoggerDomain:
    def __init__(self, node, remote_addr):
        self.remote_addr = remote_addr
        self.node = node
        self.log_level = current_app.config["POLYLOGYX_MINIMUM_OSQUERY_LOG_LEVEL"]

    def _log_status(self, data):
        current_app.logger.info("[S] Status logs for node: " + str(self.node.id))
        log_tee.handle_status(data, host_identifier=self.node.host_identifier)
        status_logs = []
        for item in data.get("data", []):
            if int(item["severity"]) < self.log_level:
                continue
            status_logs.append(StatusLog(node_id=self.node.id, **item))
        else:
            db.session.bulk_save_objects(status_logs)
            db.session.commit()
            self.node.update(
                last_status=dt.datetime.utcnow(),
                last_checkin=dt.datetime.utcnow(),
                last_ip=self.remote_addr,
            )
            db.session.add(self.node)
            db.session.commit()

    def _log_result(self, data):
        current_app.logger.info("[S] Schedule query results for node: " + str(self.node.id))
        save_and_analyze_results.apply_async(args=[data, self.node.id])
        # Further processing data and saving data will be done in celery task
        self.node.update(last_result=dt.datetime.utcnow(), last_checkin=dt.datetime.utcnow(), last_ip=self.remote_addr)
        db.session.add(self.node)
        db.session.commit()
        current_app.logger.debug("Updating the last result for node '{0}'".format(self.node))

    def log(self, data):
        log_type = data["log_type"]

        current_app.logger.debug(json.dumps(data, indent=2))

        if log_type == "status":
            self._log_status(data)
        elif log_type == "result":
            self._log_result(data)
        else:
            current_app.logger.error("%s - Unknown log_type %r", self.remote_addr, log_type)
            current_app.logger.info(json.dumps(data))
            self.node.update(last_checkin=dt.datetime.utcnow(), last_ip=self.remote_addr)
            db.session.add(self.node)
            db.session.commit()
