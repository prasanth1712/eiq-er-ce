import gzip
from functools import wraps
from io import BytesIO

from flask import current_app, jsonify, request
from sqlalchemy import and_

from polylogyx.db.models import Node
from polylogyx.extensions import db
from polylogyx.utils.esp import get_ip


def node_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from polylogyx.utils.cache import get_a_host
        # in v1.7.4, the Content-Encoding header is set when
        # --logger_tls_compress=true
        remote_addr = get_ip()
        request_json = request.get_json()

        if not request_json or "node_key" not in request_json:
            current_app.logger.error(
                "%s - Request did not contain valid JSON data. This could "
                "be an attempt to gather information about this endpoint "
                "or an automated scanner.",
                remote_addr,
            )
            # Return nothing
            return ""

        node_key = request_json.get("node_key")
        node = get_a_host(node_key=node_key)
        if not node or node.get('state') != Node.ACTIVE:
            current_app.logger.error("%s - Could not find node with node_key %s", remote_addr, node_key)
            return jsonify(node_invalid=True)

        return f(node=node, *args, **kwargs)

    return decorated_function
