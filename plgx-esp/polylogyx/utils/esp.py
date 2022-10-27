import json
from operator import itemgetter

import pika
from flask import current_app, request

from polylogyx.db.models import Config, Node, NodeConfig, Tag
from polylogyx.extensions import db
from polylogyx.utils.generic import is_wildcard_match


def push_live_query_results_to_websocket(results, queryId):

    queryId = str(queryId)
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host=current_app.config["RABBITMQ_HOST"],
            port=current_app.config["RABBITMQ_PORT"],
            credentials=current_app.config["RABBIT_CREDS"], heartbeat=300, blocked_connection_timeout=300
        )
    )
    channel = connection.channel()
    # channel.confirm_delivery()  # confirms True/False about the message delivery
    query_string = "live_query_" + queryId
    try:
        channel.basic_publish(exchange=query_string, routing_key=query_string, body=json.dumps(results))
        current_app.logger.info("Query Results for query id {} were published successfully".format(queryId))
    except Exception as e:
        current_app.logger.error(e)
    connection.close()


def assign_tags_to_node(add_tags, node_id):
    node = Node.query.filter(Node.id == node_id).first()
    for add_tag in add_tags:
        if add_tag not in node.tags:
            node.tags.append(add_tag)
    node.save()


def create_tags(*tags):
    values = []
    existing = []

    # create a set, because we haven't yet done our association_proxy in
    # sqlalchemy

    for value in (v.strip() for v in set(tags) if v.strip()):
        tag = Tag.query.filter(Tag.value == value).first()
        if not tag:
            values.append(Tag.create(value=value))
        else:
            existing.append(tag)
    else:
        if values:
            current_app.logger.info(u"Created tag{0} {1}".format(
                's' if len(values) > 1 else '',
                ', '.join(tag.value for tag in values)),
                'info')
    return values + existing


def update_mac_address(node, mac_address_obj):
    db.session.query(Node).filter(Node.id == node.id).update({"network_info": mac_address_obj})
    db.session.commit()


def update_system_info(node, system_info):
    try:
        capture_columns = set(map(itemgetter(0), current_app.config["POLYLOGYX_CAPTURE_NODE_INFO"]))
        if not capture_columns:
            return
        node_info = node.node_info
        if node_info is None:
            node_info = {}
        for column in capture_columns & set(system_info):
            if column != "cpu_brand":
                value = system_info.get(column)
                node_info[column] = value.strip()

        db.session.query(Node).filter(Node.id == node.id).update({"node_info": node_info})
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)

    return node


def update_os_info(node, system_info):
    node.os_info = system_info
    db.session.query(Node).filter(Node.id == node.id).update({"os_info": system_info})
    db.session.commit()


def update_osquery_info(node, osquery_info):
    node.host_details["osquery_info"] = osquery_info
    node.host_details["osquery_version"] = osquery_info["version"]
    db.session.query(Node).filter(Node.id == node.id).update({"host_details": node.host_details})
    db.session.commit()


def fetch_system_info(data):
    return data["system_info"]


def fetch_platform(data):
    return data["os_version"]["platform"]


def get_ip():
    route = request.access_route + [request.remote_addr]
    # trusted_proxies = {"127.0.0.1"}  # define your own set
    # remote_addr = next(
    #     (addr for addr in reversed(route) if addr not in trusted_proxies),
    #     request.remote_addr,
    # )
    if route != [request.remote_addr] and len(route) > 1:
        remote_addr = route[0]
    else:
        remote_addr = request.remote_addr
    if remote_addr == "::1":
        remote_addr = "127.0.0.1"
    elif remote_addr[:7] == "::ffff:":
        remote_addr = remote_addr[7:]

    return remote_addr


def send_checkin_queries(node):
    from polylogyx.celery.tasks import send_recon_on_checkin
    send_recon_on_checkin.apply_async(queue="default_esp_queue", args=[node.to_dict()])


def update_system_details(request_json, node):
    if "host_details" in request_json and request_json.get("host_details"):
        host_details = request_json.get("host_details")
        platform = fetch_platform(host_details)
        system_info = fetch_system_info(host_details)
        node.platform = platform
        if system_info:
            update_system_info(node, system_info)
        if "os_version" in host_details:
            update_os_info(node, host_details["os_version"])
        if "osquery_info" in host_details:
            update_osquery_info(node, host_details["osquery_info"])


def assign_config_on_enroll(enroll_json, node):
    from polylogyx.constants import DEFAULT_PLATFORMS

    hostname = None
    os_name = None
    platform = None
    if "host_details" in enroll_json:
        if "os_version" in enroll_json["host_details"] and "name" in enroll_json["host_details"]["os_version"]:
            os_name = enroll_json["host_details"]["os_version"]["name"]
        if "os_version" in enroll_json["host_details"] and "platform" in enroll_json["host_details"]["os_version"]:
            platform = enroll_json["host_details"]["os_version"]["platform"]
        if "system_info" in enroll_json["host_details"]:
            if "computer_name" in enroll_json["host_details"]["system_info"]:
                hostname = enroll_json["host_details"]["system_info"]["computer_name"]
            elif "hostname" in enroll_json["host_details"]["system_info"]:
                hostname = enroll_json["host_details"]["system_info"]["hostname"]
    if platform not in DEFAULT_PLATFORMS:
        platform = "linux"
    configs = db.session.query(Config.id, Config.conditions).filter(Config.platform == platform).all()
    matched_config_count = 0
    matched_config_id = None
    for config in configs:
        conditions = config[1]
        if conditions and parse_config_conditions(conditions, hostname, os_name):
            matched_config_id = config[0]
            matched_config_count = matched_config_count + 1
    if not matched_config_count == 1:
        # Assign default config, may be not needed as assemble_configuration does that
        default_config = db.session.query(Config).filter(Config.platform == platform).filter(Config.is_default).first()
        if default_config:
            matched_config_id = default_config.id
    node_config = db.session.query(NodeConfig).filter(NodeConfig.node == node).first()
    if node_config:
        current_app.logger.info("Retaining the exiting config of node")
    else:
        node_config = NodeConfig(config_id=matched_config_id, node_id=node.id)
        node_config.save()


def parse_config_conditions(conditions, hostname, os_name):
    is_hostname_matched, is_hostname_empty = False, False
    is_osname_matched, is_osname_empty = False, False

    if (
        "hostname" not in conditions
        or ("hostname" in conditions and "value" not in conditions["hostname"])
        or ("hostname" in conditions and "value" in conditions["hostname"] and not conditions["hostname"]["value"])
    ):
        is_hostname_empty = True
    else:
        is_hostname_matched = is_wildcard_match(hostname.lower(), conditions["hostname"]["value"].lower())
    if (
        "os_name" not in conditions
        or ("os_name" in conditions and "value" not in conditions["os_name"])
        or ("os_name" in conditions and "value" in conditions["os_name"] and not conditions["os_name"]["value"])
    ):
        is_osname_empty = True
    else:
        is_osname_matched = is_wildcard_match(os_name.lower(), conditions["os_name"]["value"].lower())

    return (
        (is_hostname_matched or is_hostname_empty)
        and (is_osname_matched or is_osname_empty)
        and (not is_hostname_empty or not is_osname_empty)
    )
