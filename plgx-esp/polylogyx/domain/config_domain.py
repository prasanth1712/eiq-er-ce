import datetime as dt

from flask import current_app

from polylogyx.db.database import db


class ConfigDomain:
    def __init__(self, node, remote_addr):
        self.node = node
        self.remote_addr = remote_addr

    def get_config(self):

        current_app.logger.info(
            "%s - %s checking in to retrieve a new configuration",
            self.remote_addr,
            self.node,
        )
        config = self.node.get_config()

        # write last_checkin, last_ip
        self.node.update(
            last_config=dt.datetime.utcnow(),
            last_checkin=dt.datetime.utcnow(),
            last_ip=self.remote_addr,
        )
        db.session.add(self.node)
        db.session.commit()

        return config
