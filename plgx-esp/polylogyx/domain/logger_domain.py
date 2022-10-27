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
        from polylogyx.utils.cache import update_cached_host
        current_app.logger.info(f"[S] Status logs for node: {str(self.node['id'])}")
        log_tee.handle_status(data, host_identifier=self.node['host_identifier'])
        status_logs = []
        for item in data.get("data", []):
            if int(item["severity"]) < self.log_level:
                continue
            status_logs.append(StatusLog(node_id=self.node['id'], **item))
        else:
            db.session.bulk_save_objects(status_logs)
            db.session.commit()
            to_update = {
                'last_status': dt.datetime.utcnow(),
                'last_checkin': dt.datetime.utcnow(),
                'last_ip': self.remote_addr
            }
            update_cached_host(self.node['node_key'], to_update)

    def _log_result(self, data):
        from polylogyx.utils.cache import update_cached_host
        current_app.logger.info(f"[S] Schedule query results for node: {str(self.node['hostname'])}")
        save_and_analyze_results.apply_async(queue='result_log_queue', args=[data, self.node])
        # Further processing data and saving data will be done in celery task
        to_update = {
            'last_result': dt.datetime.utcnow(),
            'last_checkin': dt.datetime.utcnow(),
            'last_ip': self.remote_addr
        }
        update_cached_host(self.node['node_key'], to_update)
        current_app.logger.debug(f"Updating the last result for node '<Node {self.node}>'")

    def log(self, data):
        log_type = data["log_type"]
        current_app.logger.debug(json.dumps(data, indent=2))
        if log_type == "status":
            self._log_status(data)
        elif log_type == "result":
            self._log_result(data)
        else:
            from polylogyx.utils.cache import update_cached_host
            current_app.logger.error("%s - Unknown log_type %r", self.remote_addr, log_type)
            to_update = {
                'last_checkin': dt.datetime.utcnow(),
                'last_ip': self.remote_addr
            }
            update_cached_host(self.node['node_key'], to_update)

