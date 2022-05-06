import datetime as dt
import unittest.mock as mock

from flask import url_for

from polylogyx.db.models import (DistributedQuery, DistributedQueryResult,
                                 DistributedQueryTask)

from ..factories import NodeFactory


class TestDistributedRead:
    def test_no_distributed_queries(self, db, node, testapp):
        resp = testapp.post_json(
            url_for("api.distributed_read"),
            {
                "node_key": node.node_key,
            },
            extra_environ=dict(REMOTE_ADDR="127.0.0.2"),
            expect_errors=True,
        )

        assert not resp.json["queries"]
        assert node.last_ip == "127.0.0.2"

    def test_distributed_query_read_new(self, db, node, testapp):
        q = DistributedQuery.create(sql="select * from osquery_info;")
        t = DistributedQueryTask.create(node=node, distributed_query=q)

        assert t.status == DistributedQueryTask.NEW

        resp = testapp.post_json(
            url_for("api.distributed_read"),
            {
                "node_key": node.node_key,
            },
            extra_environ=dict(REMOTE_ADDR="127.0.0.2"),
            expect_errors=True,
        )

        assert t.status == DistributedQueryTask.PENDING
        assert t.guid in resp.json["queries"]
        assert resp.json["queries"][t.guid] == q.sql
        assert t.timestamp > q.timestamp
        assert node.last_ip == "127.0.0.2"

    def test_distributed_query_read_pending(self, db, node, testapp):
        q = DistributedQuery.create(sql="select * from osquery_info;")
        t = DistributedQueryTask.create(node=node, distributed_query=q)
        t.update(status=DistributedQueryTask.PENDING)

        resp = testapp.post_json(
            url_for("api.distributed_read"),
            {
                "node_key": node.node_key,
            },
            extra_environ=dict(REMOTE_ADDR="127.0.0.2"),
            expect_errors=True,
        )

        assert not resp.json["queries"]
        assert node.last_ip == "127.0.0.2"

    def test_distributed_query_read_complete(self, db, node, testapp):
        q = DistributedQuery.create(sql="select * from osquery_info;")
        t = DistributedQueryTask.create(node=node, distributed_query=q)
        t.update(status=DistributedQueryTask.COMPLETE)

        resp = testapp.post_json(
            url_for("api.distributed_read"),
            {
                "node_key": node.node_key,
            },
            extra_environ=dict(REMOTE_ADDR="127.0.0.2"),
            expect_errors=True,
        )

        assert not resp.json["queries"]
        assert node.last_ip == "127.0.0.2"

    # def test_distributed_query_read_not_before(self, db, node, testapp):
    #     import datetime as dt

    #     now = dt.datetime.utcnow()
    #     not_before = now + dt.timedelta(days=1)

    #     q = DistributedQuery.create(
    #         sql="select * from osquery_info;", not_before=not_before
    #     )
    #     t = DistributedQueryTask.create(node=node, distributed_query=q)

    #     assert q.not_before == not_before

    #     datetime_patcher = mock.patch.object(
    #         dt, "datetime", mock.Mock(wraps=dt.datetime)
    #     )
    #     mocked_datetime = datetime_patcher.start()
    #     mocked_datetime.utcnow.return_value = not_before - dt.timedelta(seconds=1)

    #     resp = testapp.post_json(
    #         url_for("api.distributed_read"),
    #         {
    #             "node_key": node.node_key,
    #         },
    #         extra_environ=dict(REMOTE_ADDR="127.0.0.2"),
    #         expect_errors=True,
    #     )

    #     assert not resp.json["queries"]
    #     assert node.last_ip == "127.0.0.2"
    #     print("not before time - ", not_before)
    #     print("Mocked time 1 - ", mocked_datetime.utcnow.return_value)
    #     mocked_datetime.utcnow.return_value = not_before + dt.timedelta(seconds=1)
    #     print("Mocked time 2 - ", mocked_datetime.utcnow.return_value)
    #     print("Task Time  - ", t.timestamp)
    #     resp = testapp.post_json(
    #         url_for("api.distributed_read"),
    #         {
    #             "node_key": node.node_key,
    #         },
    #         extra_environ=dict(REMOTE_ADDR="127.0.0.3"),
    #         expect_errors=True,
    #     )

    #     assert t.status == DistributedQueryTask.PENDING
    #     assert t.timestamp == not_before + dt.timedelta(seconds=1)
    #     assert t.guid in resp.json["queries"]
    #     assert resp.json["queries"][t.guid] == q.sql
    #     assert node.last_ip == "127.0.0.3"

    #     datetime_patcher.stop()

    #     assert dt.datetime.utcnow() != not_before


class TestDistributedWrite:
    def test_invalid_distributed_query_id(self, db, node, testapp):
        resp = testapp.post_json(
            url_for("api.distributed_write"),
            {
                "node_key": node.node_key,
                "queries": {
                    "foo": "bar",
                },
            },
            extra_environ=dict(REMOTE_ADDR="127.0.0.2"),
            expect_errors=True,
        )
        result = DistributedQueryResult.query.filter(
            DistributedQueryResult.columns["foo"].astext == "baz"
        ).all()
        assert not result
        assert node.last_ip == "127.0.0.2"

    def test_distributed_query_write_state_new(self, db, node, testapp):
        q = DistributedQuery.create(
            sql="select name, path, pid from processes where name = 'osqueryd';"
        )
        t = DistributedQueryTask.create(node=node, distributed_query=q)

        resp = testapp.post_json(
            url_for("api.distributed_write"),
            {
                "node_key": node.node_key,
                "queries": {
                    t.guid: "",
                },
            },
            extra_environ=dict(REMOTE_ADDR="127.0.0.2"),
            expect_errors=True,
        )

        assert t.status == DistributedQueryTask.NEW
        assert not q.results
        assert node.last_ip == "127.0.0.2"

    def test_distributed_query_write_state_pending(self, db, node, testapp):
        q = DistributedQuery.create(
            sql="select name, path, pid from processes where name = 'osqueryd';"
        )
        t = DistributedQueryTask.create(node=node, distributed_query=q)
        t.update(status=DistributedQueryTask.PENDING)

        data = [
            {"name": "osqueryd", "path": "/usr/local/bin/osqueryd", "pid": "97830"},
            {"name": "osqueryd", "path": "/usr/local/bin/osqueryd", "pid": "97831"},
        ]
        # print("URL --- ",testapp.config.get["RABBITMQ_HOST"])
        resp = testapp.post_json(
            url_for("api.distributed_write"),
            {
                "node_key": node.node_key,
                "queries": {
                    t.guid: data,
                },
            },
            extra_environ=dict(REMOTE_ADDR="127.0.0.2"),
            expect_errors=True,
        )

        assert t.status == DistributedQueryTask.COMPLETE
        #        assert q.results
        #
        #         assert q.results[0].columns == data[0]
        #        assert q.results[1].columns == data[1]
        assert node.last_ip == "127.0.0.2"

    def test_distributed_query_write_state_complete(self, db, node, testapp):
        q = DistributedQuery.create(
            sql="select name, path, pid from processes where name = 'osqueryd';"
        )
        t = DistributedQueryTask.create(node=node, distributed_query=q)
        t.update(status=DistributedQueryTask.PENDING)

        data = [
            {"name": "osqueryd", "path": "/usr/local/bin/osqueryd", "pid": "97830"},
            {"name": "osqueryd", "path": "/usr/local/bin/osqueryd", "pid": "97831"},
        ]

        r = DistributedQueryResult.create(
            columns=data[0], distributed_query=q, distributed_query_task=t
        )
        t.update(status=DistributedQueryTask.COMPLETE)

        resp = testapp.post_json(
            url_for("api.distributed_write"),
            {
                "node_key": node.node_key,
                "queries": {
                    t.guid: "",
                },
            },
            extra_environ=dict(REMOTE_ADDR="127.0.0.2"),
            expect_errors=True,
        )

        # assert q.results
        # assert len(q.results) == 1
        # assert q.results[0] == r
        # assert q.results[0].columns == data[0]
        assert node.last_ip == "127.0.0.2"

    def test_distributed_query_write_state_failed(self, db, node, testapp):
        q = DistributedQuery.create(
            sql="select name, path, pid from processes where name = 'osqueryd';"
        )
        t = DistributedQueryTask.create(node=node, distributed_query=q)
        t.update(status=DistributedQueryTask.PENDING)

        data = []

        resp = testapp.post_json(
            url_for("api.distributed_write"),
            {
                "node_key": node.node_key,
                "queries": {
                    t.guid: data,
                },
                "statuses": {
                    t.guid: 2,
                },
            },
            extra_environ=dict(REMOTE_ADDR="127.0.0.2"),
            expect_errors=True,
        )

        assert t.status == DistributedQueryTask.FAILED
        # assert not q.results
        assert node.last_ip == "127.0.0.2"

    def test_malicious_node_distributed_query_write(self, db, node, testapp):
        foo = NodeFactory(
            host_identifier="foo",
            last_checkin=dt.datetime.utcnow(),
            enrolled_on=dt.datetime.utcnow(),
        )
        q1 = DistributedQuery.create(
            sql="select name, path, pid from processes where name = 'osqueryd';"
        )
        t1 = DistributedQueryTask.create(node=node, distributed_query=q1)
        q2 = DistributedQuery.create(
            sql="select name, path, pid from processes where name = 'osqueryd';"
        )
        t2 = DistributedQueryTask.create(node=foo, distributed_query=q2)

        t1.update(status=DistributedQueryTask.PENDING)
        t2.update(status=DistributedQueryTask.PENDING)
        print(node.last_checkin)
        db.session.commit()
        resp = testapp.post_json(
            url_for("api.distributed_write"),
            {"node_key": foo.node_key, "queries": {t1.guid: "bar"}},
            extra_environ=dict(REMOTE_ADDR="127.0.0.2"),
            expect_errors=True,
        )

        # assert not q1.results
        # assert not q2.results
        assert node.last_ip != "127.0.0.2"
        assert not node.last_ip
        assert foo.last_ip == "127.0.0.2"

        resp = testapp.post_json(
            url_for("api.distributed_write"),
            {"node_key": foo.node_key, "queries": {t2.guid: "bar"}},
            extra_environ=dict(REMOTE_ADDR="127.0.0.3"),
            expect_errors=True,
        )

        # assert t2.results
        assert node.last_ip != "127.0.0.2"
        assert not node.last_ip
        assert foo.last_ip == "127.0.0.3"
