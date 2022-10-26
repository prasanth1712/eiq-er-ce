import datetime as dt
import json

from flask import current_app

from polylogyx.constants import KernelQueries
from polylogyx.db.models import DistributedQueryTask, Node
from polylogyx.extensions import db
from polylogyx.utils.esp import (
    get_ip,
    push_live_query_results_to_websocket,
    update_mac_address,
    update_os_info,
    update_system_info
)
from polylogyx.utils.node import update_defender_status, get_agent_version_from_columns


class DistQueriesDomain:
    def __init__(self, node, remote_addr):
        self.node = node
        self.remote_addr = remote_addr

    def read(self):
        from polylogyx.utils.config import assemble_distributed_queries
        from polylogyx.utils.cache import update_cached_host
        current_app.logger.info(
            "%s - %s checking in to retrieve distributed queries ",
            self.remote_addr,
            f"<Node {self.node['id']}>",
        )
        queries = assemble_distributed_queries(self.node['id'])
        to_update = {
            'last_query_read': dt.datetime.utcnow(),
            'last_checkin': dt.datetime.utcnow(),
            'last_ip': self.remote_addr
        }
        update_cached_host(self.node['node_key'], to_update)
        return queries

    def write(self, data):
        from polylogyx.utils.cache import update_cached_host
        remote_addr = get_ip()
        # current_app.logger.debug(json.dumps(data, indent=2))

        queries = data.get("queries", {})
        statuses = data.get("statuses", {})

        for guid, results in queries.items():
            task = DistributedQueryTask.query.filter(
                DistributedQueryTask.guid == guid,
                DistributedQueryTask.status == DistributedQueryTask.PENDING,
                DistributedQueryTask.node_id == self.node['id'],
            ).first()

            if not task:
                current_app.logger.error(
                    "%s - Got result for distributed query not in PENDING " "state: %s",
                    remote_addr,
                    guid
                )
                continue

            # non-zero status indicates sqlite errors
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
                "Got results for query: " + str(task.distributed_query.id) + " for self.node: " + str(self.node['id'])
            )
            if task.save_results_in_db:
                node_from_db = Node.query.filter(Node.id == self.node['id']).first()
                if "system_info" in str(task.distributed_query.sql) and len(results) > 0:
                    update_system_info(node_from_db, results[0])
                elif "os_version" in str(task.distributed_query.sql) and len(results) > 0:
                    update_os_info(node_from_db, results[0])
                elif KernelQueries.MAC_ADDRESS_QUERY in str(task.distributed_query.sql) and len(results) > 0:
                    update_mac_address(node_from_db, results)
                elif "md5 from hash" in str(task.distributed_query.sql) and len(results) > 0:
                    node_host_details_to_update = get_agent_version_from_columns(results)
                    update_cached_host(self.node['node_key'], {'host_details': node_host_details_to_update})
                elif "from osquery_extensions" in str(task.distributed_query.sql) and len(results) > 0:
                    node_host_details_to_update = get_agent_version_from_columns(results)
                    update_cached_host(self.node['node_key'], {'host_details': node_host_details_to_update})
                elif "windows_security_products" in str(task.distributed_query.sql) and len(results) > 0:
                    node_host_details_to_update = update_defender_status(node_from_db, results)
                    update_cached_host(self.node['node_key'], {'host_details': node_host_details_to_update})
            else:
                data = {}
                data["node"] = {'id': self.node['id'], 'name': self.node['hostname'],
                                'host_identifier': self.node['host_identifier']}
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
            to_update = {
                'last_query_write': dt.datetime.utcnow(),
                'last_checkin': dt.datetime.utcnow(),
                'last_ip': remote_addr
            }
            update_cached_host(self.node['node_key'], to_update)
