from polylogyx.db.models import CarveSession, CarvedBlock, DashboardData
from polylogyx.domain.carves_domain import CarvesDomain

session_data = {
    "carve_id": 1,
    "carve_size": 5,
    "block_size": 10,
    "block_count": 1,
    "request_id": 100,
}
block_data = {"data": "testdata", "block_id": 1, "session_id": 10, "request_id": 100}


class TestCarvesDomain:
    def test_init(self, node):
        cd = CarvesDomain(node)
        assert cd.node == node

    def test_upload_file(self, node, db):
        cd = CarvesDomain(node)
        sid = cd.upload_file(remote_addr="127.0.0.1", data=session_data)
        assert CarveSession.query.count() > 0

    def test_upload_blocks(self,node,db):
        cd = CarvesDomain(node)
        sid = cd.upload_file(remote_addr="127.0.0.1", data=session_data)
        block_data["session_id"]=sid
        sid = CarvesDomain.upload_blocks(data=block_data)
        assert CarvedBlock.query.count() > 0
