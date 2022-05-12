# -*- coding: utf-8 -*-
from datetime import datetime

from polylogyx.db.models import Node
from polylogyx.domain.enroll_domain import EnrollDomain
from tests.conftest import db

valid_data = {
    "enroll_secret": "secret",
    "host_identifier": "3f0e144c-1f0c-11b2-a85c-ffcce65db30c",
    "platform_type": "9",
    "host_details": {
        "os_version": {
            "_id": "20.04",
            "arch": "x86_64",
            "codename": "focal",
            "major": "20",
            "minor": "04",
            "name": "Ubuntu",
            "patch": "0",
            "pid_with_namespace": "0",
            "platform": "ubuntu",
            "platform_like": "debian",
            "version": "20.04.3 LTS (Focal Fossa)",
        },
        "osquery_info": {
            "build_distro": "centos7",
            "build_platform": "linux",
            "config_hash": "",
            "config_valid": "0",
            "extensions": "active",
            "instance_id": "da67c296-796c-4bba-aae8-8c4a060e8470",
            "pid": "34140",
            "platform_mask": "9",
            "start_time": "1633957815",
            "uuid": "3f0e144c-1f0c-11b2-a85c-ffcce65db30c",
            "version": "5.0.1",
            "watcher": "34133",
        },
        "platform_info": {
            "address": "0xe000",
            "date": "06/29/2020",
            "extra": "",
            "revision": "1.21",
            "size": "16777216",
            "vendor": "LENOVO",
            "version": "R0ZET43W (1.21 )",
            "volume_size": "0",
        },
        "system_info": {
            "board_model": "20Q6S7WM00",
            "board_serial": "L1HF05T02HE",
            "board_vendor": "LENOVO",
            "board_version": "SDK0J40697 WIN",
            "computer_name": "",
            "cpu_logical_cores": "8",
            "cpu_microcode": "0xea",
            "cpu_physical_cores": "4",
            "cpu_subtype": "142",
            "cpu_type": "x86_64",
            "hardware_model": "20Q6S7WM00",
            "hardware_serial": "PF279TD9",
            "hardware_vendor": "LENOVO",
            "hardware_version": "ThinkPad L490",
            "hostname": "Prasnath",
            "local_hostname": "Prasanth",
            "physical_memory": "16418652160",
            "uuid": "3f0e144c-1f0c-11b2-a85c-ffcce65db30c",
        },
    },
}


from unittest import TestCase

from ..factories import NodeFactory


class TestEnrollDomain:
    def test_init(self):
        ed = EnrollDomain(request_json={}, remote_addr="foobar")
        assert ed.request_json == {}
        assert ed.remote_addr == "foobar"

    def test_validate(self,db):
        ed = EnrollDomain(request_json=valid_data, remote_addr="127.0.0.1")
        assert ed.validate() is True

    def test_validate_invalid_request(self):
        ed = EnrollDomain(request_json=None, remote_addr="127.0.0.1")
        assert ed.validate() is False

    def test_validate_no_enroll_secret(self, db):
        ed = EnrollDomain(
            request_json={"host_identifier": "3f0e144c-1f0c-11b2-a85c-ffcce65db30c"},
            remote_addr="127.0.0.1",
        )
        assert ed.validate() is False

    def test_validate_no_host_identifier(self, db):
        ed = EnrollDomain(
            request_json={"enroll_secret": "secret"},
            remote_addr="127.0.0.1",
        )
        assert ed.validate() is False

    def test_validate_enrolled_and_removed(self, db):
        _ = NodeFactory(host_identifier="3f0e144c-1f0c-11b2-a85c-ffcce65db30c", state=1)
        db.session.commit()
        ed = EnrollDomain(request_json=valid_data, remote_addr="127.0.0.1")
        assert ed.validate() is False

    def test_validate_enrolled_and_deleted(self, db):
        node = NodeFactory(
            host_identifier="3f0e144c-1f0c-11b2-a85c-ffcce65db30c", state=2
        )
        db.session.commit()
        ed = EnrollDomain(request_json=valid_data, remote_addr="127.0.0.1")
        ed.validate()
        assert ed.validate() is True

    def test_validate_invalid_enroll_secret(self, db):
        _ = NodeFactory(host_identifier="host", state=2)
        ed = EnrollDomain(
            request_json={"host_identifier": "host", "enroll_secret": "test"},
            remote_addr="127.0.0.1",
        )
        db.session.commit()
        assert ed.validate() is False

    def test_check_enrolled_node_with_state_delete(self, db):
        node = NodeFactory(
            host_identifier="3f0e144c-1f0c-11b2-a85c-ffcce65db30c", state=2
        )
        db.session.commit()
        ed = EnrollDomain(request_json=valid_data, remote_addr="127.0.0.1")
        assert ed.validate() is True

    def test_check_enrolled_node_with_state_active(self, db):
        node = NodeFactory(
            host_identifier="3f0e144c-1f0c-11b2-a85c-ffcce65db30c",
            enrolled_on=datetime.now(),
            state=0,
        )
        db.session.commit()
        ed = EnrollDomain(request_json=valid_data, remote_addr="127.0.0.1")
        assert ed.validate() is True
