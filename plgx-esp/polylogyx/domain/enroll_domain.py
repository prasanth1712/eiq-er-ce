import datetime as dt
import uuid

from flask import current_app
from sqlalchemy import func

from polylogyx.db.models import Node, Tag, db
from polylogyx.utils.esp import assign_config_on_enroll, send_checkin_queries, update_system_details



class EnrollDomain:
    def __init__(self, request_json, remote_addr):
        self.request_json = request_json
        self.remote_addr = remote_addr
        self.enroll_tags = set()

    def _get_node(self, state):
        node = (
            Node.query.filter(Node.state == state)
            .filter(func.lower(Node.host_identifier) == self.host_identifier.lower())
            .first()
        )
        return node

    def _add_tags(self):
        self.enroll_tags.update(current_app.config.get("POLYLOGYX_ENROLL_DEFAULT_TAGS", []))
        for value in sorted((t.strip() for t in self.enroll_tags if t)):
            tag = Tag.query.filter_by(value=value).first()
            if tag and tag not in self.node.tags:
                self.node.tags.append(tag)
            elif not tag:
                self.node.tags.append(Tag(value=value))

    def validate(self):
        # Validate request
        if not self.request_json:
            current_app.logger.error(
                "%s - Request did not contain valid JSON data. This could "
                "be an attempt to gather information about this endpoint "
                "or an automated scanner.",
                self.remote_addr,
            )
            return False

        # Inspect,validate request secret and extract tags
        self.enroll_secret = self.request_json.get(current_app.config.get("POLYLOGYX_ENROLL_OVERRIDE", "enroll_secret"))

        if not self.enroll_secret:
            current_app.logger.error("%s - No enroll_secret provided by remote host", self.remote_addr)
            return False
        else:
            if current_app.config.get("POLYLOGYX_ENROLL_SECRET_TAG_DELIMITER"):
                delimiter = current_app.config.get("POLYLOGYX_ENROLL_SECRET_TAG_DELIMITER")
                self.enroll_secret, _, self.enroll_tags = self.enroll_secret.partition(delimiter)
                self.enroll_tags = set([tag.strip() for tag in self.enroll_tags.split(delimiter)[:10]])

            if self.enroll_secret not in current_app.config["POLYLOGYX_ENROLL_SECRET"]:
                current_app.logger.error(
                    "%s - Invalid enroll_secret %s",
                    self.remote_addr,
                    self.enroll_secret,
                )
                return False

        # validate host identifier
        self.host_identifier = self.request_json.get("host_identifier", None)
        if not self.host_identifier:
            current_app.logger.error("%s - No host_identifier provided by remote host", self.remote_addr)
            return False

        if self._get_node(Node.REMOVED):
            current_app.logger.error(
                "%s - Host was enrolled already and is disabled %s",
                self.remote_addr,
                self.enroll_secret,
            )
            return False

        return True

    def enroll(self):
        from polylogyx.utils.cache import add_or_update_cached_host
        current_app.logger.info(self.request_json)
        if self.validate():
            self.node = self._get_node(Node.ACTIVE)
            now = dt.datetime.utcnow()

            if self.node:
                self.node.update(
                    last_checkin=now,
                    last_ip=self.remote_addr,
                )
                current_app.logger.info("%s -Updated existing node %s", self.remote_addr, self.node)
            else:
                db.session.execute(f"insert into node (host_identifier, last_checkin, enrolled_on, last_ip, os_info, network_info, node_key, state, node_info, host_details) select '{self.host_identifier}', '{now}', '{now}', '{self.remote_addr}', '{{}}', '{{}}', '{str(uuid.uuid4())}', 0, '{{}}', '{{}}' where not exists (select id from node where state=0 and host_identifier='{self.host_identifier}');")
                db.session.commit()
                current_app.logger.info("%s - Enrolled new self.node %s", self.remote_addr, self.node)
                self.node = self._get_node(Node.ACTIVE)
            if self.node:
                self._add_tags()
                update_system_details(self.request_json, self.node)
                assign_config_on_enroll(self.request_json, self.node)
                send_checkin_queries(self.node)
            add_or_update_cached_host(node_obj=self.node)
            return self.node.node_key, True
        return None, False