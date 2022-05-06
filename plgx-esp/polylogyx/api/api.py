# -*- coding: utf-8 -*-


from flask import Blueprint, jsonify, request

from polylogyx.domain.carves_domain import CarvesDomain
from polylogyx.domain.config_domain import ConfigDomain
from polylogyx.domain.dist_queries_domain import DistQueriesDomain
from polylogyx.domain.enroll_domain import EnrollDomain
from polylogyx.domain.logger_domain import LoggerDomain
from polylogyx.utils.decorator import node_required
from polylogyx.utils.esp import get_ip, assign_tags_to_node, create_tags

blueprint = Blueprint("api", __name__)


@blueprint.route("/")
def index():
    return ("", 204)


@blueprint.route("/enroll", methods=["POST", "PUT"])
@blueprint.route("/v1/enroll", methods=["POST", "PUT"])
def enroll():
    """
    Enroll an endpoint with osquery.
    :returns: a `node_key` unique id. Additionally `node_invalid` will
        be true if the node failed to enroll.
    """
    remote_addr = get_ip()
    request_json = request.get_json()
    node_key, node_status = EnrollDomain(request_json=request_json, remote_addr=remote_addr).enroll()
    if node_status:
        return jsonify(node_key=node_key, node_invalid=False)
    else:
        return jsonify(node_invalid=True)


@blueprint.route("/config", methods=["POST", "PUT"])
@blueprint.route("/v1/config", methods=["POST", "PUT"])
@node_required
def configuration(node=None):
    """
    Retrieve an osquery configuration for a given node.
    :returns: an osquery configuration file
    """
    remote_addr = get_ip()
    config = ConfigDomain(node=node, remote_addr=remote_addr).get_config()
    return jsonify(node_invalid=False, **config)


@blueprint.route("/log", methods=["POST", "PUT"])
@blueprint.route("/v1/log", methods=["POST", "PUT"])
@node_required
def logger(node=None):
    """ """
    remote_addr = get_ip()
    data = request.get_json()
    LoggerDomain(node=node, remote_addr=remote_addr).log(data)
    return jsonify(node_invalid=False)


@blueprint.route("/tags", methods=["POST", "PUT"])
@blueprint.route("/v1/tags", methods=["POST", "PUT"])
@node_required
def tags(node=None):
    """ """
    data = request.get_json()
    add_tags = [data.get("tag","")]
    add_tags = create_tags(*add_tags)
    assign_tags_to_node(add_tags,node)

    return jsonify(node_invalid=False)


@blueprint.route("/distributed/read", methods=["POST", "PUT"])
@blueprint.route("/v1/distributed/read", methods=["POST", "PUT"])
@node_required
def distributed_read(node=None):
    """ """
    remote_addr = get_ip()
    queries = DistQueriesDomain(node=node, remote_addr=remote_addr).read()
    return jsonify(queries=queries, node_invalid=False)


@blueprint.route("/distributed/write", methods=["POST", "PUT"])
@blueprint.route("/v1/distributed/write", methods=["POST", "PUT"])
@node_required
def distributed_write(node=None):
    """ """
    remote_addr = get_ip()
    data = request.get_json()
    DistQueriesDomain(node=node, remote_addr=remote_addr).write(data)
    return jsonify(node_invalid=False)


@blueprint.route("/start_uploads", methods=["POST", "PUT"])
@blueprint.route("/v1/start_uploads", methods=["POST", "PUT"])
@node_required
def upload_file(node=None):
    data = request.get_json()
    remote_addr = get_ip()
    sid = CarvesDomain(node).upload_file(remote_addr, data)
    return jsonify(session_id=sid)


@blueprint.route("/upload_blocks", methods=["POST", "PUT"])
@blueprint.route("/v1/upload_blocks", methods=["POST", "PUT"])
def upload_blocks(node=None):
    data = request.get_json()
    print(data)
    CarvesDomain.upload_blocks(data)
    return jsonify(node_invalid=False)


import logging
from polylogyx.utils.cache import get_log_level
from polylogyx.utils.log_setting import _set_log_level_to_db
from flask import current_app
import socket
@blueprint.route("/log_setting", methods=["PUT"])
@blueprint.route("/v1/log_setting", methods=["PUT"])
def log_setting():
    data = request.get_json()
    if "host" in data and "log_level" in data:
        try:
           ip = socket.gethostbyname(data["host"])
        except socket.gaierror:
           ip = ""
        if data["log_level"] in logging._nameToLevel and ip == request.access_route[0]:
            _set_log_level_to_db(data["log_level"])
            level = get_log_level()
            return jsonify(status="success",message="Log level changed successfully",level=level)
    return jsonify(status="failure",message="Invalid request payload")


# @blueprint.route("/test", methods=["GET"])
# def test():
#     current_app.logger.debug("debug message")
#     current_app.logger.info("info message")
#     current_app.logger.warning("warning message")
#     current_app.logger.error("error message")
#     current_app.logger.critical("critical message")
#     return jsonify(test="ok")
