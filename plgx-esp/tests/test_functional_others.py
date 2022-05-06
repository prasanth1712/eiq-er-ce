# -*- coding: utf-8 -*-
import datetime as dt
import unittest.mock as mock
from polylogyx.utils.results import learn_from_result
from .factories import NodeFactory

SAMPLE_PACK = {
    "queries": {
        "schedule": {
            "query": "select name, interval, executions, output_size, wall_time, (user_time/executions) as avg_user_time, (system_time/executions) as avg_system_time, average_memory, last_executed from osquery_schedule;",
            "interval": 7200,
            "removed": False,
            "version": "1.6.0",
            "description": "Report performance for every query within packs and the general schedule.",
        },
        "events": {
            "query": "select name, publisher, type, subscriptions, events, active from osquery_events;",
            "interval": 86400,
            "removed": False,
            "description": "Report event publisher health and track event counters.",
        },
        "osquery_info": {
            "query": "select i.*, p.resident_size, p.user_time, p.system_time, time.minutes as counter from osquery_info i, processes p, time where p.pid = i.pid;",
            "interval": 600,
            "removed": False,
            "description": "A heartbeat counter that reports general performance (CPU, memory) and version.",
        },
    }
}



class TestRuleManager:
    def test_will_load_rules_on_each_call(self, app,db):
        """
        Verifies that each call to handle_log_entry will result in a call to load_rules.
        """
        from polylogyx.utils.rules import Network

        mgr = app.rule_manager
        now = dt.datetime.utcnow()

        res_log = {
            "node_key": "556ac65e-5286-45ab-8991-a62876871ae1",
            "log_type": "result",
            "data": [
                {
                    "name": "windows_x_events",
                    "hostIdentifier": "EC25CDC2-59C5-67B3-FE6C-2DC1AA577B9A",
                    "calendarTime": "Mon Feb  1 06:23:49 2021 UTC",
                    "unixTime": 1612160629,
                    "uuid": 1222222,
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
                }
            ],
        }

        with mock.patch.object(mgr, "load_rules", wraps=lambda: []) as mock_load_rules:
            with mock.patch.object(mgr, "network", wraps=Network()) as mock_network:
                for i in range(0, 2):
                    mgr.handle_log_entry(
                        res_log["data"],
                        {"hostIdentifier": "EC25CDC2-59C5-67B3-FE6C-2DC1AA577B9A"},
                    )

                assert mock_load_rules.call_count == 2

    def test_will_reload_when_changed(self, app, db):
        from polylogyx.db.models import Rule

        mgr = app.rule_manager
        dummy_rule = {
            "id": "query_name",
            "field": "query_name",
            "type": "string",
            "input": "text",
            "operator": "equal",
            "value": "dummy-query",
        }

        now = dt.datetime.utcnow()
        next = now + dt.timedelta(minutes=5)

        # Insert a first rule.
        rule = Rule(
            name="foo",
            alerters=[],
            conditions={"condition": "AND", "rules": [dummy_rule]}
        )
        db.session.add(rule)
        db.session.commit()

        # Verify that we will reload these rules
        assert mgr.should_reload_rules() is True

        # Actually load them
        mgr.load_rules()

        # Verify that (with no changes made), we should NOT reload.
        assert mgr.should_reload_rules() is False

        # Make a change to a rule.
        rule.update(
            conditions={"condition": "OR", "rules": [dummy_rule]}, updated_at=next
        )
        db.session.add(rule)
        db.session.commit()

        # Verify that we will now reload
        assert mgr.should_reload_rules() is True


class TestLearning:
    # default columns we capture node info on are:
    COLUMNS = [
        "computer_name",
        "hardware_vendor",
        "hardware_model",
        "hardware_serial",
        "cpu_brand",
        "cpu_physical_cores",
        "physical_memory",
    ]

    def test_node_info_updated_on_added_data(self, db):
        node = NodeFactory(
        host_identifier="foobar",
        enroll_secret="secret",
        last_checkin=dt.datetime.utcnow(),
        enrolled_on=dt.datetime.utcnow(),
        platform = "linux",)
        node.save()
        assert not node.node_info

        now = dt.datetime.utcnow()
        data = [
            {
                "name": "system_info",
                "calendarTime": "%s %s" % (now.ctime(), "UTC"),
                "unixTime": now.strftime("%s"),
                "action": "added",
                "columns": {
                    "cpu_subtype": "Intel x86-64h Haswell",
                    "cpu_physical_cores": "4",
                    "physical_memory": "17179869184",
                    "cpu_logical_cores": "8",
                    "hostname": "foobar",
                    "hardware_version": "1.0",
                    "hardware_vendor": "Apple Inc.",
                    "hardware_model": "MacBookPro11,3",
                    "cpu_brand": "Intel(R) Core(TM) i7-4980HQ CPU @ 2.80GHz",
                    "cpu_type": "x86_64h",
                    "computer_name": "hostname.local",
                    "hardware_serial": "123456890",
                    "uuid": "",
                },
                "hostIdentifier": node.host_identifier,
            }
        ]

        result = {
            "node_key": node.node_key,
            "data": data,
            "log_type": "result",
        }

        learn_from_result(result, node.to_dict())

        for column in self.COLUMNS:
            assert column in node.node_info
            assert node.node_info[column] == data[0]["columns"][column]

        assert "foobar" not in node.node_info

    def test_node_info_updated_on_removed_data(self, db):
        node = NodeFactory(
        host_identifier="foobar",
        enroll_secret="secret",
        last_checkin=dt.datetime.utcnow(),
        enrolled_on=dt.datetime.utcnow(),
        platform = "linux",)
        assert not node.node_info
        node.node_info = {
            "computer_name": "barbaz",
            "hardware_version": "1.0",
            "hardware_vendor": "Apple Inc.",
            "hardware_model": "MacBookPro11,3",
            "hardware_serial": "123456890",
            "cpu_brand": "Intel(R) Core(TM) i7-4980HQ CPU @ 2.80GHz",
            "cpu_physical_cores": "4",
            "physical_memory": "17179869184",
        }
        node.save()

        now = dt.datetime.utcnow()
        data = [
            {
                "name": "computer_name",
                "hostIdentifier": "foobar.localdomain",
                "calendarTime": "Mon Jul 18 09:59:06 2016 UTC",
                "unixTime": "1468850346",
                "columns": {"computer_name": "foobar"},
                "action": "added",
            },
            {
                "name": "computer_name",
                "hostIdentifier": "foobar.localdomain",
                "calendarTime": "Mon Jul 18 09:59:06 2016 UTC",
                "unixTime": "1468850346",
                "columns": {"computer_name": "barbaz"},
                "action": "removed",
            },
            {
                "name": "computer_name",
                "hostIdentifier": "foobar.localdomain",
                "calendarTime": "Mon Jul 18 10:00:24 2016 UTC",
                "unixTime": "1468850424",
                "columns": {"computer_name": "barbaz"},
                "action": "added",
            },
            {
                "name": "computer_name",
                "hostIdentifier": "foobar.localdomain",
                "calendarTime": "Mon Jul 18 10:00:24 2016 UTC",
                "unixTime": "1468850424",
                "columns": {"computer_name": "foobar"},
                "action": "removed",
            },
            {
                "name": "computer_name",
                "hostIdentifier": "foobar.localdomain",
                "calendarTime": "Mon Jul 18 10:17:38 2016 UTC",
                "unixTime": "1468851458",
                "columns": {"computer_name": "kungpow"},
                "action": "added",
            },
            {
                "name": "computer_name",
                "hostIdentifier": "foobar.localdomain",
                "calendarTime": "Mon Jul 18 10:12:38 2016 UTC",
                "unixTime": "1468851458",
                "columns": {"computer_name": "foobar"},
                "action": "removed",
            },
            {
                "name": "computer_name",
                "hostIdentifier": "foobar.localdomain",
                "calendarTime": "Mon Jul 18 10:12:38 2016 UTC",
                "unixTime": "1468851458",
                "columns": {"computer_name": "foobar"},
                "action": "removed",
            },
            {
                "name": "computer_name",
                "hostIdentifier": "foobar.localdomain",
                "calendarTime": "Mon Jul 18 10:17:38 2016 UTC",
                "unixTime": "1468851458",
                "columns": {"computer_name": "kungpow"},
                "action": "added",
            },
        ]

        result = {
            "node_key": node.node_key,
            "data": data,
            "log_type": "result",
        }

        learn_from_result(result, node.to_dict())

        for column in self.COLUMNS:
            assert column in node.node_info

        assert node.node_info["computer_name"] == "kungpow"

        assert "foobar" not in node.node_info

    def test_node_info_not_updated_on_erroneous_data(self, db):
        node = NodeFactory(
        host_identifier="foobar",
        enroll_secret="secret",
        last_checkin=dt.datetime.utcnow(),
        enrolled_on=dt.datetime.utcnow(),
        platform = "linux",)
        assert not node.node_info

        now = dt.datetime.utcnow()
        data = [
            {
                "name": "system_info",
                "calendarTime": "%s %s" % (now.ctime(), "UTC"),
                "unixTime": now.strftime("%s"),
                "action": "added",
                "columns": {"uuid": "foobar"},
                "hostIdentifier": node.host_identifier,
            }
        ]

        result = {
            "node_key": node.node_key,
            "data": data,
            "log_type": "result",
        }

        learn_from_result(result, node.to_dict())
        assert "foobar" not in node.node_info
