from polylogyx.db.models import CarvedBlock

from flask import url_for

file_data = {
    "carve_id": 1,
    "carve_size": 5,
    "block_size": 10,
    "block_count": 10,
    "request_id": 100,
}

block_data = {"data": "testdata", "block_id": 10, "session_id": 10, "request_id": 100}

class TestCarves:
    def test_upload_file(self, node, testapp):
        file_data["node_key"]=node.node_key
        resp = testapp.post_json(
            url_for("api.upload_file"),
            params=file_data,
            extra_environ=dict(REMOTE_ADDR="127.0.0.2"),
            expect_errors=True,
        )
        assert "session_id" in resp.json

    def test_upload_blocks(self,node, testapp):
        file_data["node_key"]=node.node_key
        resp = testapp.post_json(
            url_for("api.upload_file"),
            params=file_data,
            extra_environ=dict(REMOTE_ADDR="127.0.0.2"),
            expect_errors=True,
        )
        block_data["session_id"]=resp.json["session_id"] 
        resp = testapp.post_json(
            url_for("api.upload_blocks"),
            params=block_data,
            extra_environ=dict(REMOTE_ADDR="127.0.0.2"),
            expect_errors=True,
        )
        assert CarvedBlock.query.count() > 0