from polylogyx.utils.intel import check_and_save_intel_alert, save_intel_alert
from polylogyx.db.models import Alerts


class TestIntelUtils:

    def test_check_and_save_intel_alert(self, db, result_log, result_log_scan):
        result_log_scan.result_logs.append(result_log)
        db.session.commit()
        check_and_save_intel_alert(scan_id=result_log_scan.id, scan_type=result_log_scan.scan_type,
                                   scan_value=result_log_scan.scan_value, data={}, severity='CRITICAL',
                                   source='foobar')
        alert = Alerts.query.filter(Alerts.type == Alerts.THREAT_INTEL)\
            .filter(Alerts.source == 'foobar').filter(Alerts.node_id == result_log.node_id).first()
        assert bool(alert) is True

    def test_save_intel_alert(self,db, result_log):
        save_intel_alert(data={}, source='VirusTotal', severity='CRITICAL', query_name='foobar',
                         uuid=result_log.uuid, columns={}, node_id=result_log.node_id)

        alert = Alerts.query.filter(Alerts.source == 'VirusTotal').filter(Alerts.node_id == result_log.node_id)\
            .filter(Alerts.query_name == 'foobar').first()
        assert bool(alert) is True

    def test_send_alert(self):
        pass
