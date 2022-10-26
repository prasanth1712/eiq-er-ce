# -*- coding: utf-8 -*-

from collections import namedtuple

from polylogyx.plugins.alerters.emailer import EmailAlerter
from polylogyx.utils.rules import IntelMatch, RuleMatch

from ..factories import AlertFactory

MockResponse = namedtuple("MockResponse", ["ok", "content"])


class TestEmailerAlerter:
    def setup_method(self, _method):
        self.recipients = ["test@example.com"]
        self.config = {
            "recipients": self.recipients,
            "subject_prefix": "[PolyLogyx Test]",
            "enroll_subject_prefix": "[PolyLogyx Test]",
        }

    def test_will_email_on_rule_match(self, node, rule, testapp):
        from flask_mail import email_dispatched

        alert = AlertFactory(
            message="",
            query_name="",
            node_id=1,
            rule_id=1,
            result_log_uid="",
            type="",
            source="",
            source_data="",
            severity="CRITICAL",
        )

        alert.save()
        node_dic = node.to_dict()
        node_dic["alert"] = alert

        match = RuleMatch(
            rule=rule,
            node=node.to_dict(),
            result={
                "name": "foo",
                "action": "added",
                "timestamp": "bar",
                "columns": {"boo": "baz", "kung": "bloo"},
            },
            alert_id=1,
        )

        expected_subject = (
            "[PolyLogyx Test] {host_identifier} {name} ({action})".format(
                host_identifier=node.host_identifier,
                name=rule.name,
                action=match.result["action"],
            )
        )

        @email_dispatched.connect
        def verify(message, app):
            assert message.subject == expected_subject
            assert self.recipients == message.recipients
            assert rule.name in message.body
            assert "boo" in message.body
            assert "baz" in message.body
            assert "kung = bloo" in message.body

        alerter = EmailAlerter(self.config)
        alerter.handle_alert(node_dic, match)

    def test_will_email_on_intel_match(self, node):
        from flask_mail import email_dispatched

        alert = AlertFactory(
            message="",
            query_name="",
            node_id=1,
            rule_id=None,
            result_log_uid="",
            type="",
            source="",
            source_data="",
            severity="CRITICAL",
        )

        alert.save()

        print("Alert generated - ", alert.id)

        node_dic = node.to_dict()

        node_dic["alert"] = alert

        intel = IntelMatch(
            intel="VirusTotal",
            node=node.to_dict(),
            result={
                "name": "foo",
                "action": "added",
                "timestamp": "bar",
                "columns": {"boo": "baz", "kung": "bloo"},
            },
            alert_id=1,
            data=""
        )

        expected_subject = (
            "[PolyLogyx Test] {host_identifier} {name} ({action})".format(
                host_identifier=node.host_identifier,
                name="",
                action="",
            )
        )

        @email_dispatched.connect
        def verify(message, app):
            assert message.subject == expected_subject
            assert self.recipients == message.recipients
            assert "boo" in message.body
            assert "baz" in message.body
            assert "kung = bloo" in message.body

        alerter = EmailAlerter(self.config)
        alerter.handle_alert(node=node_dic, intel_match=intel)
