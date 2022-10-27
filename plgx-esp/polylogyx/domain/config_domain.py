import datetime as dt

from flask import current_app


class ConfigDomain:
    def __init__(self, node, remote_addr):
        from polylogyx.db.models import Node
        self.node = Node.query.filter(Node.id == node['id']).first()
        self.remote_addr = remote_addr

    def get_config(self):
        from polylogyx.utils.cache import update_cached_host
        current_app.logger.info(
            "%s - %s checking in to retrieve a new configuration",
            self.remote_addr,
            self.node,
        )
        config = self.node.get_config()
        to_update = {
            'last_config': dt.datetime.utcnow(),
            'last_checkin': dt.datetime.utcnow(),
            'last_ip': self.remote_addr
        }
        update_cached_host(self.node.node_key, to_update)

        return config
