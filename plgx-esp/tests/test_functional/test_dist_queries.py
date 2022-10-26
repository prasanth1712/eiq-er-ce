import datetime as dt
import json
import time
import unittest.mock as mock

from flask import url_for

from polylogyx.db.models import (DistributedQuery, DistributedQueryTask)

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
    #
    #     now = dt.datetime.utcnow()
    #     not_before = now + dt.timedelta(days=1)
    #
    #     q = DistributedQuery.create(
    #         sql="select * from osquery_info;", not_before=not_before
    #     )
    #     t = DistributedQueryTask.create(node=node, distributed_query=q)
    #
    #     assert q.not_before == not_before
    #
    #     datetime_patcher = mock.patch.object(
    #         dt, "datetime", mock.Mock(wraps=dt.datetime)
    #     )
    #     mocked_datetime = datetime_patcher.start()
    #     mocked_datetime.utcnow.return_value = not_before - dt.timedelta(seconds=1)
    #
    #     resp = testapp.post_json(
    #         url_for("api.distributed_read"),
    #         {
    #             "node_key": node.node_key,
    #         },
    #         extra_environ=dict(REMOTE_ADDR="127.0.0.2"),
    #         expect_errors=True,
    #     )
    #
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
    #
    #     assert t.status == DistributedQueryTask.PENDING
    #     assert t.timestamp == not_before + dt.timedelta(seconds=1)
    #     assert t.guid in resp.json["queries"]
    #     assert resp.json["queries"][t.guid] == q.sql
    #     assert node.last_ip == "127.0.0.3"
    #
    #     datetime_patcher.stop()
    #
    #     assert dt.datetime.utcnow() != not_before


class TestDistributedWrite:
    def test_distributed_write_normal_case(self, db, node, testapp, channel):
        query_obj = DistributedQuery.create(sql="foo")
        task_obj = DistributedQueryTask.create(node=node, distributed_query=query_obj)
        assert task_obj.status == DistributedQueryTask.NEW
        guid = task_obj.guid

        # Creating all the necessary queues and exchanges for the live query
        exchange_name = f'live_query_{query_obj.id}'
        channel.exchange_declare(exchange=exchange_name, auto_delete=True)
        result = channel.queue_declare(queue=exchange_name, exclusive=False,
                                       arguments={'x-message-ttl':  120 * 1000,
                                                  'x-expires': 120 * 1000})
        queue_name = result.method.queue
        channel.queue_bind(exchange=exchange_name, queue=queue_name)

        # Making distributed/read request to mark the task to pending state
        resp = testapp.post_json(
            url_for("api.distributed_read"),
            {
                "node_key": node.node_key
            },
            extra_environ=dict(REMOTE_ADDR="127.0.0.2"),
            expect_errors=True,
        )
        resp = testapp.post_json(
            url_for("api.distributed_write"),
            {
                "node_key": node.node_key,
                "queries": {
                    guid: [{}],
                },
            },
            extra_environ=dict(REMOTE_ADDR="127.0.0.2"),
            expect_errors=True,
        )

        # Read the message from rabbitMQ queue
        body = None
        time_now = time.time()
        for method, properties, body in channel.consume(exchange_name, inactivity_timeout=120 * 1000):
            if body:
                body = json.loads(body)
                break
            elif time.time() - time_now > 60 * 1:
                break
        # delete queue and exchange
        channel.stop_consuming()
        channel.exchange_delete(exchange_name)
        channel.queue_delete(exchange_name)
        assert 'node' in body and 'id' in body['node'] and body['node']['id'] == node.id
        task = DistributedQueryTask.query.filter(DistributedQueryTask.guid == guid).first()
        assert task.status == DistributedQueryTask.COMPLETE
        assert node.last_ip == "127.0.0.2"

    def test_distributed_write_with_out_read(self, db, node, testapp):
        query_obj = DistributedQuery.create(sql="foo")
        task_obj = DistributedQueryTask.create(node=node, distributed_query=query_obj)
        task_obj.status = DistributedQueryTask.PENDING
        guid = task_obj.guid
        resp = testapp.post_json(
            url_for("api.distributed_write"),
            {
                "node_key": node.node_key,
                "queries": {
                    guid: [{}],
                },
            },
            extra_environ=dict(REMOTE_ADDR="127.0.0.2"),
            expect_errors=True,
        )
        task = DistributedQueryTask.query.filter(DistributedQueryTask.guid == guid).first()
        assert task.status == DistributedQueryTask.COMPLETE
        assert node.last_ip == "127.0.0.2"

    def test_distributed_query_write_state_new(self, db, node, testapp):
        query_obj = DistributedQuery.create(sql="foo")
        task_obj = DistributedQueryTask.create(node=node, distributed_query=query_obj)
        guid = task_obj.guid
        resp = testapp.post_json(
            url_for("api.distributed_write"),
            {
                "node_key": node.node_key,
                "queries": {
                    guid: [{}],
                },
            },
            extra_environ=dict(REMOTE_ADDR="127.0.0.2"),
            expect_errors=True,
        )
        task = DistributedQueryTask.query.filter(DistributedQueryTask.guid == guid).first()
        assert task.status == DistributedQueryTask.NEW
        assert node.last_ip == "127.0.0.2"

    def test_distributed_query_write_state_pending(self, db, node, testapp):
        query_obj = DistributedQuery.create(sql="foo")
        task_obj = DistributedQueryTask.create(node=node, distributed_query=query_obj)
        task_obj.status = DistributedQueryTask.PENDING
        guid = task_obj.guid
        resp = testapp.post_json(
            url_for("api.distributed_write"),
            {
                "node_key": node.node_key,
                "queries": {
                    guid: [{}],
                },
            },
            extra_environ=dict(REMOTE_ADDR="127.0.0.2"),
            expect_errors=True,
        )
        task = DistributedQueryTask.query.filter(DistributedQueryTask.guid == guid).first()
        assert task.status == DistributedQueryTask.COMPLETE
        assert node.last_ip == "127.0.0.2"

    def test_distributed_query_write_state_failed(self, db, node, testapp):
        query_obj = DistributedQuery.create(sql="foo")
        task_obj = DistributedQueryTask.create(node=node, distributed_query=query_obj)
        task_obj.status = DistributedQueryTask.PENDING
        guid = task_obj.guid
        resp = testapp.post_json(
            url_for("api.distributed_write"),
            {
                "node_key": node.node_key,
                "queries": {
                    "foo": [{}],
                },
            },
            extra_environ=dict(REMOTE_ADDR="127.0.0.2"),
            expect_errors=True,
        )
        task = DistributedQueryTask.query.filter(DistributedQueryTask.guid == guid).first()
        assert task.status != DistributedQueryTask.COMPLETE
        assert node.last_ip == "127.0.0.2"
