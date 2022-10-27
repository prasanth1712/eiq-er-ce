import datetime as dt
import gzip
import io
import json

from flask import url_for
from polylogyx.db.models import ResultLog
import time


class TestLogging:
    def test_bad_post_request(self, node, testapp):
        resp = testapp.post(url_for("api.logger"), {"foo": "bar"}, expect_errors=True)
        assert not resp.normal_body

    def test_missing_node_key(self, node, testapp):
        resp = testapp.post_json(
            url_for("api.logger"), {"foo": "bar"}, expect_errors=True
        )
        assert not resp.normal_body
        # assert resp.json == {'node_invalid': True}

    def test_status_log_created_for_node(self, node, testapp):
        data = {
            "line": 1,
            "message": "This is a test of the emergency broadcast system.",
            "severity": 1,
            "filename": "foobar.cpp",
        }

        assert not node.status_logs.count()

        resp = testapp.post_json(
            url_for("api.logger"),
            {
                "node_key": node.node_key,
                "data": [data],
                "log_type": "status",
            },
            extra_environ=dict(REMOTE_ADDR="127.0.0.2"),
            expect_errors=True,
        )

        assert node.status_logs.count()
        assert node.status_logs[0].line == data["line"]
        assert node.status_logs[0].message == data["message"]
        assert node.status_logs[0].severity == data["severity"]
        assert node.status_logs[0].filename == data["filename"]
        assert node.last_ip == "127.0.0.2"

    def test_status_log_created_for_node_put(self, node, testapp):
        data = {
            "line": 1,
            "message": "This is a test of the emergency broadcast system.",
            "severity": 1,
            "filename": "foobar.cpp",
        }

        assert not node.status_logs.count()

        resp = testapp.put_json(
            url_for("api.logger"),
            {
                "node_key": node.node_key,
                "data": [data],
                "log_type": "status",
            },
            extra_environ=dict(REMOTE_ADDR="127.0.0.2"),
            expect_errors=True,
        )

        assert node.status_logs.count()
        assert node.status_logs[0].line == data["line"]
        assert node.status_logs[0].message == data["message"]
        assert node.status_logs[0].severity == data["severity"]
        assert node.status_logs[0].filename == data["filename"]
        assert node.last_ip == "127.0.0.2"

    def test_status_log_created_for_node_when_gzipped(self, node, testapp):
        data = {
            "line": 1,
            "message": "This is a test of the emergency broadcast system.",
            "severity": 1,
            "filename": "foobar.cpp",
        }

        assert not node.status_logs.count()
        payload_data = json.dumps(
                {
                    "node_key": node.node_key,
                    "data": [data],
                    "log_type": "status",
                })

        fileobj = io.BytesIO()
        gzf = gzip.GzipFile(fileobj=fileobj, mode="wb")
        gzf.write(
            payload_data.encode("utf-8")
        )
        gzf.close()

        resp = testapp.post(
            url_for("api.logger"),
            fileobj.getvalue(),
            # payload_data,
            headers={"Content-Encoding": "gzip", "Content-Type": "application/json"},
            extra_environ=dict(REMOTE_ADDR="127.0.0.2"),
            expect_errors=True,
        )

        assert node.status_logs.count()
        assert node.status_logs[0].line == data["line"]
        assert node.status_logs[0].message == data["message"]
        assert node.status_logs[0].severity == data["severity"]
        assert node.status_logs[0].filename == data["filename"]
        assert node.last_ip == "127.0.0.2"

    def test_no_status_log_created_when_data_is_empty(self, node, testapp,celery_worker):
        assert not node.status_logs.count()
        with celery_worker:
            resp = testapp.post_json(
                url_for("api.logger"),
                {
                    "node_key": node.node_key,
                    "data": [],
                    "log_type": "status",
                },
                extra_environ=dict(REMOTE_ADDR="127.0.0.2"),
                expect_errors=True,
            )

            assert not node.status_logs.count()
            assert node.last_ip == "127.0.0.2"

    def test_result_log_created_for_node(self,testapp,db,node,celery_worker):
        now = dt.datetime.utcnow()
        data = [
            {
                "diffResults": {
                    "added": [
                        {
                            "name": "osqueryd",
                            "path": "/usr/local/bin/osqueryd",
                            "pid": "97830",
                        }
                    ],
                    "removed": [
                        {
                            "name": "osqueryd",
                            "path": "/usr/local/bin/osqueryd",
                            "pid": "97650",
                        }
                    ],
                },
                "name": "processes",
                "hostIdentifier": "hostname.local",
                "calendarTime": "%s %s" % (now.ctime(), "UTC"),
                "unixTime": now.strftime("%s"),
            }
        ]

        assert not node.result_logs.count()
        with celery_worker:
            resp = testapp.post_json(
                url_for("api.logger"),
                {
                    "node_key": node.node_key,
                    "data": data,
                    "log_type": "result",
                },
                extra_environ=dict(REMOTE_ADDR="127.0.0.2"),
                expect_errors=True,
            )

            time.sleep(5)
            assert node.result_logs.count() == 2
            assert node.last_ip == "127.0.0.2"

            added = ResultLog.query.filter(ResultLog.node==node).filter(ResultLog.action=="added").first()
            removed = ResultLog.query.filter(ResultLog.node==node).filter(ResultLog.action=="removed").first()

            assert added.name == data[0]["name"]
            assert added.columns == data[0]["diffResults"]["added"][0]
            assert removed.name == data[0]["name"]
            assert removed.columns == data[0]["diffResults"]["removed"][0]

    def test_no_result_log_created_when_data_is_empty(self, node, testapp):
        assert not node.result_logs.count()

        resp = testapp.post_json(
            url_for("api.logger"),
            {
                "node_key": node.node_key,
                "data": [],
                "log_type": "result",
            },
            extra_environ=dict(REMOTE_ADDR="127.0.0.2"),
            expect_errors=True,
        )

        assert not node.result_logs.count()
        # assert node.last_ip == "127.0.0.2"

    def test_result_event_format(self,testapp,db,node,celery_worker):
        now = dt.datetime.utcnow()
        calendarTime = "%s %s" % (now.ctime(), "UTC")
        unixTime = now.strftime("%s")

        data = [
            {
                "action": "added",
                "columns": {
                    "name": "osqueryd",
                    "path": "/usr/local/bin/osqueryd",
                    "pid": "97830",
                },
                "name": "osquery",
                "hostIdentifier": "hostname.local",
                "calendarTime": calendarTime,
                "unixTime": unixTime,
            },
            {
                "action": "removed",
                "columns": {
                    "name": "osqueryd",
                    "path": "/usr/local/bin/osqueryd",
                    "pid": "97830",
                },
                "name": "osquery",
                "hostIdentifier": "hostname.local",
                "calendarTime": calendarTime,
                "unixTime": unixTime,
            },
            {
                "action": "added",
                "columns": {
                    "name": "osqueryd",
                    "path": "/usr/local/bin/osqueryd",
                    "pid": "97830",
                },
                "name": "processes",
                "hostIdentifier": "hostname.local",
                "calendarTime": calendarTime,
                "unixTime": unixTime,
            },
            {
                "action": "removed",
                "columns": {
                    "name": "osqueryd",
                    "path": "/usr/local/bin/osqueryd",
                    "pid": "97830",
                },
                "name": "processes",
                "hostIdentifier": "hostname.local",
                "calendarTime": calendarTime,
                "unixTime": unixTime,
            },
        ]

        assert not node.result_logs.count()
        with celery_worker:
            resp = testapp.post_json(
                url_for("api.logger"),
                {
                    "node_key": node.node_key,
                    "data": data,
                    "log_type": "result",
                },
                extra_environ=dict(REMOTE_ADDR="127.0.0.2"),
                expect_errors=True,
            )
            time.sleep(5)
            assert node.result_logs.count() == 4
            assert node.last_ip == "127.0.0.2"

            added = ResultLog.query.filter(ResultLog.node==node).filter(ResultLog.action=="added").count()
            removed = ResultLog.query.filter(ResultLog.node==node).filter(ResultLog.action=="removed").count()
            assert added == 2
            assert removed == 2

    def test_heterogeneous_result_format(self,testapp,db,node,celery_worker):

        now = dt.datetime.utcnow()
        calendarTime = "%s %s" % (now.ctime(), "UTC")
        unixTime = now.strftime("%s")

        data = [
            {
                "action": "removed",
                "columns": {
                    "name": "osqueryd",
                    "path": "/usr/local/bin/osqueryd",
                    "pid": "97830",
                },
                "name": "processes",
                "hostIdentifier": "hostname.local",
                "calendarTime": calendarTime,
                "unixTime": unixTime,
            },
            {
                "diffResults": {
                    "added": [
                        {
                            "name": "osqueryd",
                            "path": "/usr/local/bin/osqueryd",
                            "pid": "97830",
                        }
                    ],
                    "removed": [
                        {
                            "name": "osqueryd",
                            "path": "/usr/local/bin/osqueryd",
                            "pid": "97650",
                        }
                    ],
                },
                "name": "processes",
                "hostIdentifier": "hostname.local",
                "calendarTime": calendarTime,
                "unixTime": unixTime,
            },
            {
                "calendarTime": calendarTime,
                "unixTime": unixTime,
                "action": "snapshot",
                "snapshot": [
                    {"parent": "0", "path": "/sbin/launchd", "pid": "1"},
                    {"parent": "1", "path": "/usr/sbin/syslogd", "pid": "51"},
                    {"parent": "1", "path": "/usr/libexec/UserEventAgent", "pid": "52"},
                    {"parent": "1", "path": "/usr/libexec/kextd", "pid": "54"},
                ],
                "name": "process_snapshot",
                "name": "file_events",
                "hostIdentifier": "hostname.local",
            },
        ]

        assert not node.result_logs.count()
        with celery_worker:
            resp = testapp.post_json(
                url_for("api.logger"),
                {
                    "node_key": node.node_key,
                    "data": data,
                    "log_type": "result",
                },
                extra_environ=dict(REMOTE_ADDR="127.0.0.2"),
                expect_errors=True,
            )
            time.sleep(10)
            assert node.result_logs.count() == 7
            assert node.last_ip == "127.0.0.2"

        