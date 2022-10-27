import unittest.mock as mock
import datetime as dt
from polylogyx.plugins.intel.ibmxforce import IBMxForceIntel
from polylogyx.db.models import ThreatIntelCredentials,Settings,ResultLogScan,VirusTotalAvEngines,ResultLog,Alerts


class TestibmxforceIntel:
   def setup_method(self, _method):
        self.name = "ibmxforce"
        self.config = {
                "level": "error",
        }

   def test_init_method(self):
       ibm=IBMxForceIntel(self.config)
       assert ibm.name == 'ibmxforce'
       assert ibm.api_keys_added is False

   def test_update_credentials(self,db):
        # inserting cred
        cred={"key": "foo", "pass": "bar"}
        ibm = ThreatIntelCredentials(
            intel_name='ibmxforce',
            credentials=cred
        )
        db.session.add(ibm)
        db.session.commit()
        ibm = IBMxForceIntel(self.config)
        ibm.update_credentials()
        assert ibm.name == 'ibmxforce'
        assert ibm.api_keys_added is True
        assert ibm.key == 'foo'
        assert ibm.api_pass == 'bar'

   def test_send_request(self,db):
       result_log_scan= ResultLogScan(scan_type='md5',
                                         scan_value='foobar',
                                         reputations={}
                                         )
       cred = {"key": "foo", "pass": "bar"}
       ibm = ThreatIntelCredentials(
           intel_name='ibmxforce',
           credentials=cred
       )
       db.session.add(result_log_scan)
       db.session.add(ibm)
       ibm = IBMxForceIntel(self.config)
       ibm.update_credentials()
       resp=mock.Mock(**{'status_code':200,'json.return_value':{'malware':{'risk':'high'}}})

       with mock.patch('requests.get',return_value=resp) as pmock:
            ibm.send_request('https://dummyurl',result_log_scan,'md5')

       pmock.called
       assert result_log_scan.reputations['ibmxforce_detected'] is True

   def test_send_request_with_400_response(self,db):
       result_log_scan= ResultLogScan(scan_type='md5',
                                         scan_value='foobar',
                                         reputations={}
                                         )
       cred = {"key": "foo", "pass": "bar"}
       ibm = ThreatIntelCredentials(
           intel_name='ibmxforce',
           credentials=cred
       )
       db.session.add(result_log_scan)
       db.session.add(ibm)
       ibm = IBMxForceIntel(self.config)
       ibm.update_credentials()
       resp=mock.Mock(**{'status_code':400,'json.return_value':{'malware':{'risk':'high'}}})

       with mock.patch('requests.get',return_value=resp) as pmock:
            ibm.send_request('https://dummyurl',result_log_scan,'md5')

       pmock.called
       assert result_log_scan.reputations == {}

   def test_send_request_with_401_response(self, db):
       result_log_scan = ResultLogScan(scan_type='md5',
                                       scan_value='foobar',
                                       reputations={}
                                       )
       cred = {"key": "foo", "pass": "bar"}
       ibm = ThreatIntelCredentials(
           intel_name='ibmxforce',
           credentials=cred
       )
       db.session.add(result_log_scan)
       db.session.add(ibm)
       ibm = IBMxForceIntel(self.config)
       ibm.update_credentials()
       resp = mock.Mock(**{'status_code': 400, 'json.return_value': {'malware': {'risk': 'high'}}})

       with mock.patch('requests.get', return_value=resp) as pmock:
           ibm.send_request('https://dummyurl', result_log_scan, 'md5')

       pmock.called
       assert result_log_scan.reputations == {}

   def test_analyse_pending_hash(self,db):
       result_log_scan= ResultLogScan(scan_type='md5',
                                         scan_value='foobar',
                                         reputations={}
                                         )
       cred = {"key": "foo", "pass": "bar"}
       ibm = ThreatIntelCredentials(
           intel_name='ibmxforce',
           credentials=cred
       )
       db.session.add(result_log_scan)
       db.session.add(ibm)
       ibm = IBMxForceIntel(self.config)
       ibm.update_credentials()
       resp=mock.Mock(**{'status_code':200,'json.return_value':{'malware':{'risk':'high'}}})

       with mock.patch('requests.get',return_value=resp) as pmock:
            ibm.analyse_pending_hashes()

       pmock.called
       assert result_log_scan.reputations['ibmxforce_detected'] is True

   def test_vt_genearte_alerts(self, db, node):
       result_log = ResultLog(
           name='dummy',
           node=node,
           uuid='foobar',
           timestamp=dt.datetime.utcnow(),
           columns={'md5': 'foobar'}
       )
       result_log_scan = ResultLogScan(scan_type='md5',
                                       scan_value='foobar',
                                       reputations={'ibmxforce': {'malware':{'risk':'high'}},
                                                    'ibmxforce_detected': True})

       db.session.add(result_log)
       db.session.add(result_log_scan)
       result_log_scan.result_logs.append(result_log)
       db.session.commit()
       ibm =  IBMxForceIntel(self.config)
       with mock.patch('polylogyx.utils.intel.send_alert') as pmock:
           ibm.generate_alerts()
       alert = Alerts.query.all()[0]
       assert pmock.called
       assert alert.source == 'ibmxforce'
       assert alert.node_id == node.id
       assert alert.source_data == result_log_scan.reputations['ibmxforce']
