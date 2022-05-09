# -*- coding: utf-8 -*-
import datetime as dt
import json

from flask import current_app

from polylogyx.constants import DEFAULT_PLATFORMS
from polylogyx.db.database import db
from polylogyx.db.models import Config, DefaultFilters, DefaultQuery, Node, NodeConfig, ReleasedAgentVersions


def get_config_of_node(node):
    platform = node.platform
    if platform not in DEFAULT_PLATFORMS:
        platform = "linux"
    node_config = db.session.query(NodeConfig).filter(NodeConfig.node == node).first()
    if node_config:
        return node_config.config
    else:
        return db.session.query(Config).filter(Config.platform == platform).filter(Config.is_default).first()


def get_node_health(node):
    checkin_interval = current_app.config["POLYLOGYX_CHECKIN_INTERVAL"]
    if isinstance(checkin_interval, (int, float)):
        checkin_interval = dt.timedelta(seconds=checkin_interval)
    if (dt.datetime.utcnow() - node.last_checkin) > checkin_interval:
        return u"danger"
    else:
        return ""


def append_node_information_to_result_log(node, input):
    output = dict(input)
    try:
        output["platform"] = node["platform"]
        output["last_checkin"] = node["last_checkin"]
        output["is_active"] = node["is_active"]
        output["last_ip"] = node["last_ip"]

        if "os_info" in node:
            os_info = node["os_info"]
            output["osname"] = os_info.get("name", "")
            if "version" in os_info:
                output["version"] = os_info["version"]
        if "node_info" in node:
            node_info = node["node_info"]

            output["computername"] = node_info["computer_name"]
            output["hardware_model"] = node_info["hardware_model"]
            output["hardware_vendor"] = node_info["hardware_vendor"]
            output["cpu_physical_cores"] = node_info["cpu_physical_cores"]
    except Exception as e:
        current_app.logger.error(e)

    return output


def append_node_and_rule_information_to_alert(node, input):
    output = dict(input)
    print(type(node))
    try:
        output["platform"] = node["platform"]
        output["is_active"] = node["is_active"]
        output["last_ip"] = node["last_ip"]
        output["platform"] = node["platform"]

        if "os_info" in node:
            os_info = node["os_info"]
            output["osname"] = os_info["name"]
        # if "network_info" in node:
        #    network_info = node["network_info"]
        #    output["macaddress"] = network_info["mac_address"]
        if "node_info" in node:
            print("ok")
            node_info = node["node_info"]
            output["computername"] = node_info["computer_name"]
            output["hardware_model"] = node_info["hardware_model"]
    except Exception as e:
        print(e)
    return output


def update_defender_status(node, columns):
    host_details = node.host_details
    data = {}
    if columns:
        host_details["windows_security_products_status"] = {}
        for column in columns:
            key = column["name"] + "_" + column["type"]
            host_details["windows_security_products_status"][key] = column
        current_app.logger.info(
            "Windows defender details fetched  for node %s are %s", node.host_identifier, json.dumps(host_details)
        )
    else:
        current_app.logger.info("Unable to update the defender status %s", node)
    db.session.query(Node).filter(Node.id == node.id).update({"host_details": host_details})
    db.session.commit()


def update_osquery_or_agent_version(node, columns):
    if not isinstance(columns, list):
        columns = [columns]
    host_details = node.host_details
    for column_dict in columns:
        if "md5" in column_dict:
            platform = node.platform
            if not platform == "windows" and not platform == "darwin" and not platform == "freebsd":
                platform = "linux"
            arch = DefaultQuery.ARCH_x64
            if (
                node.node_info
                and "cpu_type" in node.node_info
                and node.node_info["cpu_type"] == DefaultFilters.ARCH_x86
            ):
                arch = DefaultQuery.ARCH_x86

            agent_version_obj = (
                ReleasedAgentVersions.query.filter(ReleasedAgentVersions.extension_hash_md5 == column_dict["md5"])
                .filter(ReleasedAgentVersions.platform == platform)
                .filter(ReleasedAgentVersions.arch == arch)
                .first()
            )
            if agent_version_obj:
                host_details["extension_version"] = agent_version_obj.extension_version
                current_app.logger.info(
                    "Extension details fetched for node %s are %s", node.host_identifier, json.dumps(host_details)
                )
        elif "version" in column_dict and "type" in column_dict:
            if column_dict["type"] == "core":
                host_details["osquery_version"] = column_dict["version"]
                current_app.logger.info("Agent Os Query details updated for node %s", node.host_identifier)
            elif column_dict["type"] == "extension" and column_dict["name"] in [
                "plgx_linux_extension",
                "plgx_win_extension",
                "plgx_mac_extension",
                "plgx_extension"
            ]:
                host_details["extension_version"] = column_dict["version"]
                current_app.logger.info("Agent extension details updated for node %s", node.host_identifier)
            else:
                current_app.logger.error("Unable to update the osquery/extension version %s", node)
            current_app.logger.info(
                "OSQuery/Extension Version is fetched for node %s are %s",
                node.host_identifier,
                json.dumps(host_details),
            )
        else:
            current_app.logger.error("Unable to update the osquery/extension version %s", node)
    db.session.query(Node).filter(Node.id == node.id).update({"host_details": host_details})
    db.session.commit()
