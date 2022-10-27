# -*- coding: utf-8 -*-
"""Defines fixtures available to all tests."""

import datetime as dt

import pytest
from webtest import TestApp

import manage
from polylogyx.application import create_app
from polylogyx.db.database import db as _db
from polylogyx.db.models import NodeConfig,Config
from polylogyx.db.models import *
from polylogyx.settings import TestConfig

from .factories import NodeFactory, RuleFactory, PackFactory, QueryFactory, TagFactory, DistributedQueryFactory, \
    DistributedQueryTaskFactory, ResultLogFactory, ResultLogScanFactory


@pytest.fixture(scope="function")
def app():
    """An application for the tests."""
    _app = manage.app
    ctx = _app.test_request_context()
    ctx.push()

    try:
        yield _app
    finally:
        ctx.pop()


@pytest.fixture(scope="function")
def api():
    """An api instance for the tests, no manager"""
    import os

    # the mere presence of the env var should prevent the manage
    # blueprint from being registered
    os.environ["POLYLOGYX_NO_MANAGER"] = "1"

    _app = create_app(config=TestConfig)
    ctx = _app.test_request_context()
    ctx.push()

    try:
        yield _app
    finally:
        ctx.pop()


@pytest.fixture(scope="function")
def testapp(app):
    """A Webtest app."""
    return TestApp(app=app, extra_environ=dict(REMOTE_ADDR="127.0.0.1"))


@pytest.fixture(scope="function")
def client(api):
    with api.test_client() as client:
        yield client


@pytest.fixture(scope="function")
def testapi(api):
    return TestApp(api)


@pytest.fixture(scope="function")
def db(app):
    """A database for the tests."""
    _db.app = app
    with app.app_context():
        _db.drop_all()
        _db.create_all()

    yield _db

    # Explicitly close DB connection
    _db.session.close()
    _db.drop_all()


@pytest.fixture(scope="function")
def channel(app):
    import pika, ssl
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=current_app.config['RABBITMQ_HOST'],
                                                                   port=current_app.config['RABBITMQ_PORT'],
                                                                   credentials=current_app.config['RABBIT_CREDS'],
                                                                   ssl=current_app.config['RABBITMQ_USE_SSL'],
                                                                   ssl_options={"cert_reqs": ssl.CERT_NONE}))
    channel = connection.channel()
    return channel


@pytest.fixture(scope="function")
def node(db):
    """A node for the tests."""
    node = NodeFactory(
        host_identifier="foobar",
        enroll_secret="secret",
        last_checkin=dt.datetime.utcnow(),
        enrolled_on=dt.datetime.utcnow(),
        platform = "linux",
        node_info = {"cpu_type": "x86_64h", "computer_name": "INBGNL0354", "hardware_model": "MacBookPro16,1", "hardware_serial": "C02GC5YNMD6M", "hardware_vendor": "Apple Inc.", "physical_memory": "17179869184", "cpu_physical_cores": "6"},
        os_info = {"arch": "x86_64", "name": "ubuntu", "build": "21A559", "major": "12", "minor": "0", "patch": "1", "version": "12.0.1", "codename": "test", "platform": "linux", "platform_like": "linux"},
        network_info = {"mac": "88:66:5a:53:6c:ec", "mask": "ffff:ffff:ffff:ffff::", "address": "fe80::ff:4bda:f863:56c9%en0", "enabled": "", "description": "", "manufacturer": "", "connection_id": "", "connection_status": ""}
        )

    config = Config(name="Default Config", platform="linux")
    config.save()
    df = DefaultFilters(filters={'foo': "foobar"}, platform='linux', created_at=dt.datetime.utcnow(),
                        config_id=config.id)
    df.save()
    dq = DefaultQuery(name='foo', platform='linux', sql='foobar', config_id=config.id, status=True)
    dq.save()
    node_config = NodeConfig(node_id=node.id,config_id=config.id)
    node_config.save()
    db.session.commit()
    return node


@pytest.fixture(scope="function")
def rule(db):
    rule = RuleFactory(
        name="testrule", description="kung = $kung", alerters=[], conditions={}
    )
    db.session.commit()
    return rule


@pytest.fixture(scope='function')
def celery_app(app):
    from polylogyx.celery.tasks import celery
    # for use celery_worker fixture
    from celery.contrib.testing import tasks  # NOQA
    from polylogyx.extensions import make_celery
    celery = make_celery(app, celery)
    return celery


@pytest.fixture(scope='function')
def celery_worker(celery_app):
    from celery.contrib.testing.worker import start_worker
    celery_worker = start_worker(celery_app, perform_ping_check=False, concurrency=2)
    return celery_worker


@pytest.fixture(scope="function")
def otx():
    from OTXv2 import OTXv2
    key = '69f922502ee0ea958fa0ead2979257bd084fa012c283ef9540176ce857ac6f2c'
    otx = OTXv2(key)
    return otx


@pytest.fixture(scope="function")
def pack(db):
    pack = PackFactory(
        name="test_pack", description="kung = $kung", platform='linux'
    )
    db.session.commit()
    return pack


@pytest.fixture(scope="function")
def query(db):
    query = QueryFactory(
        name="test_query", description="kung = $kung", sql='foobar'
    )
    db.session.commit()
    return query


@pytest.fixture(scope="function")
def tag(db):
    tag = TagFactory(
        value="test_tag"
    )
    db.session.commit()
    return tag


@pytest.fixture(scope="function")
def distributed_query(db, node):
    query = DistributedQueryFactory(
        sql='foobar'
    )
    db.session.commit()
    task = DistributedQueryTaskFactory(node=node, distributed_query=query)
    db.session.commit()
    return query


@pytest.fixture(scope="function")
def result_log(db, node):
    import uuid
    result_log = ResultLogFactory(name='test_query', node_id=node.id, uuid=uuid.uuid4())
    db.session.commit()
    return result_log


@pytest.fixture(scope="function")
def result_log_scan(db, node, result_log):
    result_log_scan = ResultLogScanFactory(scan_type='foo', scan_value='foobar', reputations={})
    db.session.commit()
    return result_log_scan

