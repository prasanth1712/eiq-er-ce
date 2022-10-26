# -*- coding: utf-8 -*-
import datetime as dt
import json

from flask import current_app

from polylogyx.constants import DEFAULT_PLATFORMS
from polylogyx.db.database import db
from polylogyx.db.models import Config, DefaultFilters, DefaultQuery, Node, NodeConfig


def get_config_of_node(node):
    platform = node.platform
    if platform not in DEFAULT_PLATFORMS:
        platform = "linux"
    node_config = db.session.query(NodeConfig).filter(NodeConfig.node == node).first()
    if node_config:
        return node_config.config
    else:
        return db.session.query(Config).filter(Config.platform == platform).filter(Config.is_default).first()


def append_node_information_to_result_log(node, input):
    output = dict(input)
    try:
        output['_platform'] = node.get('platform',"")
        output['_ip_address'] = node.get('last_ip',"")

        if 'os_info' in node:
            os_info = node['os_info']
            output['_os_name'] = os_info.get('name',"")
            output['_os_version'] = os_info.get('version')
        if 'network_info' in node:
            network_info = node['network_info']
            output['_macaddress'] = network_info.get('mac_address',"")
        if 'node_info' in node:
            node_info = node['node_info']

            output['_computer_name'] = node_info.get('computer_name',"")
            output['_hardware_model'] = node_info.get('hardware_model',"")
            output['_hardware_vendor'] = node_info.get('hardware_vendor',"")
            output['_cpu_physical_cores'] = node_info.get('cpu_physical_cores',"")
    except Exception as e:
        print(e)
    return output


def append_node_and_rule_information_to_alert(node, input):
    output = dict(input)
    try:
        output['_platform'] = node.get('platform',"")
        output['_ip_address'] = node.get('last_ip',"")

        if 'os_info' in node:
            os_info = node['os_info']
            output['_os_name'] = os_info.get('name',"")
            output['_os_version'] = os_info.get('version')

        if 'network_info' in node:
            network_info = node['network_info']
            output['_macaddress'] = network_info.get('mac_address',"")
        if 'node_info' in node:
            node_info = node['node_info']

            output['_computer_name'] = node_info.get('computer_name',"")
            output['_hardware_model'] = node_info.get('hardware_model',"")
            output['_hardware_vendor'] = node_info.get('hardware_vendor',"")
            output['_cpu_physical_cores'] = node_info.get('cpu_physical_cores',"")
    except Exception as e:
        print(e)
    return output


def update_defender_status(node, columns):
    host_details = {}
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
    return host_details


def get_agent_version_from_columns(columns):
    versions_dict = {}
    if not isinstance(columns, list):
        columns = [columns]
    for column_dict in columns:
        if "version" in column_dict and "type" in column_dict:
            if column_dict["type"] == "core":
                versions_dict["osquery_version"] = column_dict["version"]
            elif column_dict["type"] == "extension" and column_dict["name"] in [
                "plgx_linux_extension",
                "plgx_win_extension",
                "plgx_mac_extension",
                "plgx_extension"
            ]:
                versions_dict["extension_version"] = column_dict["version"]
    return versions_dict

