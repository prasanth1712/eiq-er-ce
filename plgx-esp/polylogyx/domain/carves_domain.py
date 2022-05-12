import datetime as dt
import random
import string

from sqlalchemy import and_

from polylogyx.celery.tasks import build_carve_session_archive
from polylogyx.db.models import CarvedBlock, CarveSession
from polylogyx.extensions import db


class CarvesDomain:
    def __init__(self, node):
        self.node = node

    def upload_file(self, remote_addr, data):
        sid = "".join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10))
        CarveSession.create(
            node_id=self.node.id,
            session_id=sid,
            carve_guid=data["carve_id"],
            status=CarveSession.StatusInProgress,
            carve_size=data["carve_size"],
            block_size=data["block_size"],
            block_count=data["block_count"],
            request_id=data["request_id"],
        )
        self.node.update(last_checkin=dt.datetime.utcnow(), last_ip=remote_addr)
        db.session.add(self.node)
        db.session.commit()
        return sid

    def upload_blocks(data):
        carveSession = CarveSession.query.filter(CarveSession.session_id == data["session_id"]).first_or_404()

        if CarvedBlock.query.filter(
            and_(
                CarvedBlock.session_id == data["session_id"],
                CarvedBlock.block_id == data["block_id"],
            )
        ).first():
            return
        size = len(data["data"])

        CarvedBlock.create(
            data=data["data"],
            block_id=data["block_id"],
            session_id=data["session_id"],
            request_id=data["request_id"],
            size=size,
        )
        carveSession.completed_blocks = carveSession.completed_blocks + 1

        # Are we expecting to receive more blocks?
        if carveSession.completed_blocks < carveSession.block_count:
            carveSession.update(carveSession)
            db.session.commit()

            print("Gathering more blocks")
            # return jsonify(node_invalid=False)
            return
        carveSession.status = CarveSession.StatusBuilding
        # If not, let's reassemble everything

        db.session.commit()
        build_carve_session_archive.apply_async(queue="default_esp_queue", args=[carveSession.session_id])
        # debug("File successfully carved to: %s" % out_file_name)
