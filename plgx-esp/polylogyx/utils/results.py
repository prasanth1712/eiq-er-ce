# -*- coding: utf-8 -*-

import datetime as dt
import json
import uuid
from collections import namedtuple
from operator import itemgetter

from flask import current_app

from polylogyx.constants import DefaultInfoQueries
from polylogyx.db.models import Node
from polylogyx.utils.node import update_osquery_or_agent_version

Field = namedtuple("Field", ["name", "action", "columns", "timestamp", "uuid"])


def learn_from_result(result, node):
    if not result["data"]:
        return

    capture_columns = set(map(itemgetter(0), current_app.config["POLYLOGYX_CAPTURE_NODE_INFO"]))

    if not capture_columns:
        return

    node_info = node.get("node_info", {})
    orig_node_info = node_info.copy()

    for (
        _,
        action,
        columns,
        _,
        _,
    ) in extract_results(result):
        # only update columns common to both sets
        for column in capture_columns & set(columns):

            cvalue = node_info.get(column)  # current value
            value = columns.get(column)

            if action == "removed" and (cvalue is None or cvalue != value):
                pass
            elif action == "removed" and cvalue == value:
                node_info.pop(column)
            elif action == "added" and (cvalue is None or cvalue != value):
                node_info[column] = value

    # only update node_info if there's actually a change

    if orig_node_info == node_info:
        return

    node = Node.get_by_id(node["id"])
    node.update(node_info=node_info)
    return


def process_result(result, node):
    if not result["data"]:
        current_app.logger.error("No results to process from %s", node)
        return
    data = []
    for name, action, columns, timestamp, uuid in extract_results(result):
        try:
            if name not in DefaultInfoQueries.DEFAULT_VERSION_INFO_QUERIES.keys():
                if name == "windows_real_time_events":
                    message = json.loads(columns["data"])
                    del columns["data"]
                    columns.update(message)
                if "script_text" in columns:
                    columns["script_text"] = columns["script_text"].replace("\\x0D", "\n").replace("\\x0A", "\r")
                data.append(
                    {
                        "name": name,
                        "uuid": uuid,
                        "action": action,
                        "columns": columns,
                        "timestamp": timestamp,
                        "node_id": node.id,
                    }
                )
            else:
                update_osquery_or_agent_version(node, columns)
        except Exception as e:
            current_app.logger.error("Unable to update the agent version details %s and the error is %s", node, str(e))
    return data


def extract_results(result):
    """
    extract_results will convert the incoming log data into a series of Fields,
    normalizing and/or aggregating both batch and event format into batch
    format, which is used throughout the rest of polylogyx.
    """
    if not result["data"]:
        return

    timefmt = "%a %b %d %H:%M:%S %Y UTC"
    strptime = dt.datetime.strptime

    for entry in result["data"]:

        if "uuid" not in entry:
            entry["uuid"] = str(uuid.uuid4())

        name = entry["name"]

        timestamp = strptime(entry["calendarTime"], timefmt)

        if "columns" in entry:
            yield Field(
                name=name, action=entry["action"], columns=entry["columns"], timestamp=timestamp, uuid=entry["uuid"]
            )

        elif "diffResults" in entry:
            added = entry["diffResults"]["added"]
            removed = entry["diffResults"]["removed"]
            for (action, items) in (("added", added), ("removed", removed)):
                # items could be "", so we're still safe to iter over
                # and ensure we don't return an empty value for columns
                for columns in items:
                    yield Field(name=name, action=action, columns=columns, timestamp=timestamp, uuid=entry["uuid"])

        elif "snapshot" in entry:
            for columns in entry["snapshot"]:
                yield Field(name=name, action="snapshot", columns=columns, timestamp=timestamp, uuid=entry["uuid"])

        else:
            current_app.logger.error("Encountered a result entry that " "could not be processed! %s", json.dumps(entry))


def extract_result_logs(result):
    """
    extract_results will convert the incoming log data into a series of Fields,
    normalizing and/or aggregating both batch and event format into batch
    format, which is used throughout the rest of polylogyx.
    """
    Field = namedtuple("Field", ["name", "action", "columns", "timestamp", "uuid", "node_id"])

    timefmt = "%a %b %d %H:%M:%S %Y UTC"
    strptime = dt.datetime.strptime

    for data in result["data"]:

        if "uuid" not in data:
            data["uuid"] = str(uuid.uuid4())

        timestamp = strptime(data["calendarTime"], timefmt)

        yield Field(
            name=data["name"],
            action=data["action"],
            columns=data["columns"],
            timestamp=timestamp,
            uuid=data["uuid"],
            node_id=data["node_id"],
        )
