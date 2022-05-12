from polylogyx.db.models import ResultLog, StatusLog
from polylogyx.domain.logger_domain import LoggerDomain
from time import sleep
data_status = {
    "node_key": "556ac65e-5286-45ab-8991-a62876871ae1",
    "log_type": "status",
    "data": [
        {
            "line": 100,
            "message": "Removed 33 event batches (with 18446744073709551606 delete errors)  for subscriber: openbsm.socket_events (limit: 2500, last query: never)",
            "severity": 1,
            "filename": "eventsubscriberplugin.cpp",
            "created": "2021-11-11 11:43:24.772856",
            "version": "4.7.0",
        }
    ],
}


data_result = {
    "node_key": "556ac65e-5286-45ab-8991-a62876871ae1",
    "log_type": "result",
    "data": [
        {
            "name": "windows_x_events",
            "hostIdentifier": "EC25CDC2-59C5-67B3-FE6C-2DC1AA577B9A",
            "calendarTime": "Mon Feb  1 06:23:49 2021 UTC",
            "unixTime": 1612160629,
            "epoch": 0,
            "counter": 0,
            "numerics": False,
            "columns": {
                "action": "FILE_WRITE",
                "eid": "7F90B2D2-C5CB-42B4-9D34-F20E0FE3FFFF",
                "target_path": "",
                "md5": "780af610d9d4356384f32af1fae80e4a",
                "sha256": "d8c574eeb904425f51a6a4e337e",
                "hashed": "1",
                "uid": "BUILTIN\\\\Administrators",
                "time": "1612320986",
                "utc_time": "Wed Feb  3 02:56:26 2021\\n",
                "pe_file": "NO",
                "pid": "1168",
                "process_guid": "2FFEA365-6565-11EB-82BD-02CC6CC956C2",
                "amsi_is_malware": "NO",
                "byte_stream": "test",
            },
            "action": "added",
        }
    ],
}


class TestLoggerDomain:
    def test_init(self, node):
        ld = LoggerDomain(node=node, remote_addr="127.0.0.1")
        assert ld.node == node

    def test_log_result(self,db,node,celery_worker):
        ld = LoggerDomain(node=node, remote_addr="127.0.0.1")
        ld._log_result(data_result)
        sleep(5)
        records = ResultLog.query.count()
        assert records > 0

    def test_log_status(self, db, node):
        ld = LoggerDomain(node=node, remote_addr="127.0.0.2")
        ld._log_status(data_status)
        db.session.commit()
        records = StatusLog.query.count()
        assert records > 0

    def test_log(self,db,node,celery_worker):
        ld = LoggerDomain(node=node, remote_addr="127.0.0.2")
        ld.log(data_status)
        ld.log(data_result)
        temp_data = data_status.copy()
        temp_data["log_type"] = "other"
        ld.log(temp_data)
        assert True
        sleep(5)
        db.session.commit()
        records = ResultLog.query.count()
        assert records > 0
        records = StatusLog.query.count()
        assert records > 0

    def test_log_status_negative_severity(self, db, node):
        ld = LoggerDomain(node=node, remote_addr="127.0.0.2")
        temp_data = data_status.copy()
        temp_data["data"][0]["severity"] = -1
        ld._log_status(temp_data)
        db.session.commit()
        records = StatusLog.query.count()
        assert records == 0
