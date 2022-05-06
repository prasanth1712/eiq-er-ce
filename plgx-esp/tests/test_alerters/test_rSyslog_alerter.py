import datetime as dt
import unittest.mock as mock
import raven
from polylogyx.plugins.alerters.rsyslog import RsyslogAlerter
from polylogyx.utils.rules import IntelMatch, RuleMatch
from ..factories import AlertFactory


class TestRsyslogAlerter:

     def setup_method(self, _method):
         self.service_key = "foobar"
         self.config = {
                          "service_key": self.service_key,
                      }

     def test_will_alert_on_rule_match(self, node, rule, testapp):
         match = RuleMatch(
             rule=rule,
             node=node.to_dict(),
             result={
                 "name": "foo",
                 "action": "added",
                 "timestamp": dt.datetime.utcnow(),
                 "columns": {"boo": "baz", "kung": "bloo"},
             },
             alert_id=1,
         )

         with mock.patch("socket.socket.connect", return_value={"status":True}) as pmock_sock:
             with mock.patch("socket.socket.send") as pmock:
                 alerter = RsyslogAlerter(self.config)
                 alerter.handle_alert(node.to_dict(), match,None)
         assert pmock.called
         assert pmock_sock.called

     def test_will_alert_on_intel_match(self, node, rule, testapp):
         alert = AlertFactory(
             message="",
             query_name="",
             node_id=1,
             rule_id=None,
             recon_queries="",
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
         intel = {"type": 'THREAT_INTEL', "source": 'VirusTotal', "severity": 'LOW', "query_name": 'dummy'}
         intel = IntelMatch(
             intel=intel,
             node=node.to_dict(),
             result={
                 "name": "foo",
                 "action": "added",
                 "timestamp": "bar",
                 "columns": {"boo": "baz", "kung": "bloo"},
             },
             data="",
             alert_id=1,
         )

         with mock.patch("socket.socket.connect", return_value={"status":True}) as pmock_sock:
             with mock.patch("socket.socket.send") as pmock:
                 alerter = RsyslogAlerter(self.config)
                 alerter.handle_alert(node.to_dict(), None,intel)
         assert pmock.called
         assert pmock_sock.called