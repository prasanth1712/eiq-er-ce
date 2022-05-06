import datetime as dt
import json

from flask import current_app

from polylogyx.constants import KernelQueries
from polylogyx.db.models import DistributedQueryTask
from polylogyx.extensions import db
from polylogyx.utils.esp import (
    get_ip,
    push_live_query_results_to_websocket,
    update_mac_address,
    update_os_info,
    update_system_info
)
from polylogyx.utils.node import update_defender_status, update_osquery_or_agent_version


class DistQueriesDomain:
    def __init__(self, node, remote_addr):
        self.node = node
        self.remote_addr = remote_addr

    def read(self):

        current_app.logger.info(
            "%s - %s checking in to retrieve distributed queries",
            self.remote_addr,
            self.node,
        )

        queries = self.node.get_new_queries()

        self.node.update(
            last_query_read=dt.datetime.utcnow(),
            last_checkin=dt.datetime.utcnow(),
            last_ip=self.remote_addr,
        )
        db.session.add(self.node)
        db.session.commit()

        return queries

    def write(self, data):
        remote_addr = get_ip()

        current_app.logger.debug(json.dumps(data, indent=2))

        queries = data.get("queries", {})
        statuses = data.get("statuses", {})

        for guid, results in queries.items():
            task = DistributedQueryTask.query.filter(
                DistributedQueryTask.guid == guid,
                DistributedQueryTask.status == DistributedQueryTask.PENDING,
                DistributedQueryTask.node == self.node,
            ).first()

            if not task:
                current_app.logger.error(
                    "%s - Got result for distributed query not in PENDING " "state: %s: %s",
                    remote_addr,
                    guid,
                    json.dumps(data),
                )
                continue

            # non-zero status indicates sqlite errors
            current_app.logger.info(statuses)
            current_app.logger.info(results)
            if not statuses.get(guid, 0):
                status = DistributedQueryTask.COMPLETE
            else:
                current_app.logger.error(
                    "%s - Got non-zero status code (%d) on distributed query %s",
                    remote_addr,
                    statuses.get(guid),
                    guid,
                )
                status = DistributedQueryTask.FAILED
            current_app.logger.info(
                "Got results for query: " + str(task.distributed_query.id) + " for self.node: " + str(self.node.id)
            )
            if task.save_results_in_db:
                if task.distributed_query.alert:
                    task.data = results
                if "system_info" in str(task.distributed_query.sql) and len(results) > 0:
                    update_system_info(self.node, results[0])
                elif "os_version" in str(task.distributed_query.sql) and len(results) > 0:
                    update_os_info(self.node, results[0])
                elif KernelQueries.MAC_ADDRESS_QUERY in str(task.distributed_query.sql) and len(results) > 0:
                    update_mac_address(self.node, results)
                elif "md5 from hash" in str(task.distributed_query.sql) and len(results) > 0:
                    update_osquery_or_agent_version(self.node, results)
                elif "from osquery_extensions" in str(task.distributed_query.sql) and len(results) > 0:
                    update_osquery_or_agent_version(self.node, results)
                elif "windows_security_products" in str(task.distributed_query.sql) and len(results) > 0:
                    update_defender_status(self.node, results)
            else:
                data = {}
                self.node_data = {"id": self.node.id}
                if self.node.node_info and "computer_name" in self.node.node_info:
                    self.node_data["name"] = self.node.node_info["computer_name"]
                else:
                    current_app.logger.error("System name is empty")
                    self.node_data["host_identifier"] = self.node.host_identifier

                data["node"] = self.node_data
                data["data"] = results
                data["query_id"] = task.distributed_query.id
                if not statuses.get(guid, 0):
                    data["status"] = 0
                else:
                    data["status"] = 1

                push_live_query_results_to_websocket(data, task.distributed_query.id)

            task.status = status
            task.updated_at = dt.datetime.utcnow()
            db.session.add(task)

        else:
            self.node.update(
                last_query_write=dt.datetime.utcnow(),
                last_checkin=dt.datetime.utcnow(),
                last_ip=remote_addr,
            )
            db.session.add(self.node)
            db.session.commit()
