# -*- coding: utf-8 -*-
"""Defines fixtures available to all tests."""
import json

import pytest
from webtest import TestApp

from polylogyx.application import create_app
from polylogyx.database import db as _db
from polylogyx.settings import TestConfig


from .factories import (
    NodeFactory, RuleFactory, UserFactory, DashboardDataFactory, AlertsFactory, ResultLogFactory,
    StatusLogFactory, CarveSessionFactory,
    DistributedQueryFactory, DistributedQueryTaskFactory)


@pytest.yield_fixture(scope='function')
def app():
    """An application for the tests."""
    _app = create_app(config=TestConfig)
    ctx = _app.test_request_context()
    ctx.push()

    try:
        yield _app
    finally:
        ctx.pop()


@pytest.fixture(scope='function')
def client(app):
    return app.test_client()


@pytest.yield_fixture(scope='function')
def api():
    """An api instance for the tests, no manager"""
    import os
    # the mere presence of the env var should prevent the manage
    # blueprint from being registered
    os.environ['POLYLOGYX_NO_MANAGER'] = '1'

    _app = create_app(config=TestConfig)
    ctx = _app.test_request_context()
    ctx.push()

    try:
        yield _app
    finally:
        ctx.pop()


@pytest.fixture(scope='function')
def testapp(app):
    """A Webtest app."""
    return TestApp(app)


@pytest.fixture(scope='function')
def testapi(api):
    return TestApp(api)


@pytest.yield_fixture(scope='function')
def db(app):
    """A database for the tests."""
    _db.app = app
    with app.app_context():
        _db.create_all()

    yield _db

    # Explicitly close DB connection
    _db.session.close()
    _db.drop_all()


@pytest.fixture
def url_prefix():
    return "/services/api/v1"


@pytest.fixture
def token(client, user, url_prefix):
    data = {'username': 'admin', 'password': 'admin'}
    res = client.post(url_prefix + '/login', data=json.dumps(data), headers={'Accept': None})
    return json.loads(res.data)['token']


@pytest.fixture
def node(db):
    """A node for the tests."""
    node = NodeFactory(host_identifier='foobar', enroll_secret='foobar', platform='windows', node_info={}, os_info={}, network_info={}, host_details={})
    db.session.commit()
    return node


@pytest.fixture
def status_log(db):
    """A Status Log row for the tests."""
    log = StatusLogFactory()
    db.session.commit()
    return log


@pytest.fixture
def rule(db):
    """A rule for the tests."""
    rule = RuleFactory(
        name='testrule',
        description='kung = $kung',
        alerters=[],
        conditions={}
    )
    db.session.commit()
    return rule


@pytest.fixture
def user(db):
    user = UserFactory(
        username='admin',
        password='admin'
    )
    db.session.commit()
    return user


@pytest.fixture
def dashboard_data(db):
    data = {"top_queries": {"cpu_time": 21640, "pack/test_pack_automation_1/test_query": 100947,
                            "per_query_perf": 99279, "test_query": 87728, "win_dns_events": 24214}}
    dashboard_data = DashboardDataFactory(
        name='dashboard',
        data=data
    )
    db.session.commit()
    return dashboard_data


@pytest.fixture
def alerts(db, node, rule):
    """An alert for the tests."""
    message = {
        "eid": "2334C7E0-16CF-486A-AF58-E40884ACFFFF", "md5": "44d88612fea8a8f36de82e1278abb02f",
        "pid": "16856", "uid": "LAPTOP-RSVR4441user", "time": "1576575204", "action": "FILE_RENAME",
        "hashed": "1", "sha256": "275a021bbfb6489e54d471899f7db9d1663fc695ec2fe2a2c4538aabf651fd0f",
        "pe_file": "NO", "utc_time": "Tue Dec 17 09:33:24 2019 UTC",
        "target_path": "C:\\Users\\user\\Downloads\\eicar.com.txt [Orig: C:\\Users\\user\\Downloads\\eicar.com.txt.crdownload]",
        "process_guid": "CFA60AEC-1D78-11EA-9CAD-A4C3F0975828", "process_name": "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe"
    }
    source_data = {
        "md5": "44d88612fea8a8f36de82e1278abb02f", "sha1": "3395856ce81f2b7382dee72602f798b642f14140",
        "scans": {"AVG": {"result": "EICAR Test-NOT virus!!!", "update": "20191217",
                          "version": "18.4.3895.0", "detected": True},
                  "CMC": {"result": "Eicar.test.file", "update": "20190321", "version": "1.1.0.977",
                          "detected": True},
                  "MAX": {"result": "malware (ai score=100)", "update": "20191217",
                          "version": "2019.9.16.1", "detected": True},
                  "Avast": {"result": "EICAR Test-NOT virus!!!", "update": "20191217",
                            "version": "18.4.3895.0", "detected": True},
                  "Avira": {"result": "Eicar-Test-Signature", "update": "20191217",
                            "version": "8.3.3.8", "detected": True},
                  "Panda": {"result": "EICAR-AV-TEST-FILE", "update": "20191216",
                            "version": "4.6.4.2", "detected": True},
                  "VBA32": {"result": "EICAR-Test-File", "update": "20191217",
                            "version": "4.3.0", "detected": True},
                  "VIPRE": {"result": "EICAR (v)", "update": "20191217",
                            "version": "80094", "detected": True},
                  "Malwarebytes": {"result": None, "update": "20191217",
                                   "version": "2.1.1.1115", "detected": False},
                  "SymantecMobileInsight": {"result": "ALG:EICAR Test String", "update": "20191030",
                                            "version": "2.0", "detected": True}
                  },
        "total": 64, "sha256": "275a021bbfb6489e54d471899f7db9d1663fc695ec2fe2a2c4538aabf651fd0f",
        "scan_id": "275a021bbfb6489e54d471899f7db9d1663fc695ec2fe2a2c4538aabf651fd0f-1576574303",
        "resource": "44d88612fea8a8f36de82e1278abb02f",
        "permalink": "https://www.virustotal.com/file/275a021bbfb6489e54d471899f7db9d1663fc695ec2fe2a2c4538aabf651fd0f/analysis/1576574303/",
        "positives": 63, "scan_date": "2019-12-17 09:18:23",
        "verbose_msg": "Scan finished, information embedded", "response_code": 1
    }
    alerts1_message = {
        "eid": "692744BC-2EB0-4EF7-B4AA-DB5400000000", "md5": "", "pid": "10596",
        "uid": "BUILTIN\\Administrators", "time": "1576500444", "action": "FILE_DELETE", "hashed": "0",
        "sha256": "", "pe_file": "NO", "utc_time": "Mon Dec 16 12:47:24 2019 UTC",
        "target_path": "C:\\Users\\Administrator\\Downloads\\sample.jar",
        "process_guid": "3A4A7E16-1FCB-11EA-82AC-A8AFF0EAAE41",
        "process_name": "C:\\Windows\\System32\\cmd.exe"
    }
    alerts = AlertsFactory(
        query_name='win_file_events',
        message=message,
        node_id=1,
        rule_id=1,
        severity='LOW',
        type='Threat Intel',
        result_log_uid='f41d1a87-557a-4bbf-9e60-ed1c03265634',
        source='virustotal',
        source_data=source_data
    )

    alerts1 = AlertsFactory(
        query_name='win_file_events',
        message=alerts1_message,
        node_id=1,
        rule_id=1,
        severity='INFO',
        type='rule',
        result_log_uid='ac11ae27-59a5-47c9-9a05-f17e335f04f9',
        source='rule',
        source_data={}
    )

    db.session.commit()
    # return alerts


@pytest.fixture
def result_log(db):
    columns1 = {
        "action": "PROC_CREATE", "cmdline": "\"C:\\Windows\\system32\\NOTEPAD.EXE\" C:\\Users\\user\\Downloads\\eicar.com.txt",
        "eid": "12AD1BF2-D65B-4C72-AC0B-895F07F8FFFF", "owner_uid": "LAPTOP-RSVR4441\\user",
        "parent_path": "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
        "parent_pid": "16856",
        "parent_process_guid": "CFA60AEC-1D78-11EA-9CAD-A4C3F0975828",
        "path": "C:\\Windows\\System32\\notepad.exe",
        "pid": "4280",
        "process_guid": "CFA60C9B-1D78-11EA-9CAD-A4C3F0975828",
        "time": "1576574927",
        "utc_time": "Tue Dec 17 09:28:47 2019 UTC"
    }
    columns2 = {
      "action": "PROC_CREATE",
      "cmdline": "\"C:\\Windows\\system32\\NOTEPAD.EXE\" C:\\Users\\user\\Downloads\\eicar.com.txt",
      "eid": "12AD1BF2-D65B-4C72-AC0B-895F07F8FFFF",
      "owner_uid": "LAPTOP-RSVR4441\\user",
      "parent_path": "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
      "parent_pid": "16856",
      "parent_process_guid": "CFA60AEC-1D78-11EA-9CAD-A4C3F0975828",
      "path": "C:\\Windows\\System32\\notepad.exe",
      "pid": "4280",
      "process_guid": "CFA60C9B-1D78-11EA-9CAD-A4C3F0975828",
      "time": "1576574927",
      "utc_time": "Tue Dec 17 09:28:47 2019 UTC",
      "md5": "X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*"
    }
    columns3 = {
      "action": "PROC_CREATE",
      "cmdline": "\"C:\\Windows\\system32\\NOTEPAD.EXE\" C:\\Users\\user\\Downloads\\eicar.com.txt",
      "eid": "12AD1BF2-D65B-4C72-AC0B-895F07F8FFFF",
      "owner_uid": "LAPTOP-RSVR4441\\user",
      "parent_path": "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
      "parent_pid": "16856",
      "parent_process_guid": "CFA60AEC-1D78-11EA-9CAD-A4C3F0975828",
      "path": "C:\\Windows\\System32\\notepad.exe",
      "pid": "4280",
      "process_guid": "CFA60C9B-1D78-11EA-9CAD-A4C3F0975828",
      "time": "1576574927",
      "utc_time": "Tue Dec 17 09:28:47 2019 UTC",
      "md5": "X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*"
    }
    result_log1 = ResultLogFactory(
        name='kernel_modules',
        action='added',
        columns=columns1,
        node_id=1,
        status=2
    )
    result_log2 = ResultLogFactory(
        name='kernel_modules',
        action='added',
        columns=columns2,
        node_id=1,
        status=2
    )
    result_log3 = ResultLogFactory(
        name='kernel_modules',
        action='added',
        columns=columns3,
        node_id=1,
        status=2
    )
    db.session.commit()
    # return result_log


@pytest.fixture
def carve_session(db, node):
    carve_session = CarveSessionFactory(
        node_id=1,
        session_id='MQIAPXX285',
        carve_guid='42bd2230-490a-4b1f-8c51-0d26d7b6542e',
        carve_size=4608,
        block_size=30000,
        block_count=1,
        completed_blocks=1,
        archive='MQIAPXX28542bd2230-490a-4b1f-8c51-0d26d7b6542e.tar',
        request_id='62d5510f-ae98-46c1-8bdc-f84abad3b4fa',
        status='COMPLETED'
    )
    db.session.commit()
    return carve_session


@pytest.fixture
def distributed_query(db):
    distributed_query = DistributedQueryFactory(
        description='system_info',
        sql='select * from system_info'
    )
    db.session.commit()
    return distributed_query


@pytest.fixture
def distributed_query_task(db, distributed_query):
    distributed_query_task2 = DistributedQueryTaskFactory(
        save_results_in_db=True,
        distributed_query_id=1,
        guid='62d5510f-ae98-46c1-8bdc-f84abad3b4fa',
        node_id=1
    )
    db.session.commit()
    return distributed_query_task
