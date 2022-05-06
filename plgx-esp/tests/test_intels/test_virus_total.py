import unittest.mock as mock
import datetime as dt
from polylogyx.plugins.intel.virustotal import VTIntel
from polylogyx.db.models import ThreatIntelCredentials,Settings,ResultLogScan,VirusTotalAvEngines,ResultLog,Alerts

class TestVirusTotalIntel:

   def setup_method(self, _method):
        self.name = "virustotal"
        self.config = {
            "name": self.name
        }

   def test_update_credentials(self,db):

        # Insert credentials

        vt = ThreatIntelCredentials(
            intel_name='virustotal',
            credentials= {"key": "foo"}
        )
        db.session.add(vt)
        db.session.commit()
        with mock.patch("polylogyx.plugins.intel.virustotal.VirusTotalPublicApi", return_value=True) as pmock:
            vt= VTIntel(self.config)
            vt.update_credentials()
        assert pmock.called

   def test_analyse_pending_hash(self,db):

       # Insert data for result_log_scan,min_match_count,virustotal_av_engines

       result_log_scan = ResultLogScan(scan_type='md5',
                                       scan_value='foo',
                                       reputations={}
                                       )
       settings= Settings(name='virustotal_min_match_count',
                          setting=1,
                          created_at=dt.datetime.now())

       av_engines_1= VirusTotalAvEngines(name='boo',status=True)
       av_engines_2= VirusTotalAvEngines(name='baz',status=False)
       vt = ThreatIntelCredentials(
           intel_name='virustotal',
           credentials={"key": "foo"}
       )
       db.session.add(vt)
       db.session.add(result_log_scan)
       db.session.add(settings)
       db.session.add(av_engines_1)
       db.session.add(av_engines_2)
       resp={'response_code':200,'results':{'positives':1,'resource':'foo','scans':{'boo':{'detected':True},'baz':{'detected':False}}}}
       with mock.patch("polylogyx.plugins.intel.virustotal.VirusTotalPublicApi.get_file_report", return_value=resp) as pmock:
           vt = VTIntel(self.config)
           vt.update_credentials()
           vt.analyse_pending_hashes()
       assert pmock.called
       assert result_log_scan.reputations['virustotal_detected'] is True

   def test_analyse_pending_multiple_hashes(self, db):
       # Insert data for result_log_scan,min_match_count,virustotal_av_engines

       result_log_scan_1 = ResultLogScan(scan_type='md5',
                                       scan_value='foo',
                                       reputations={}
                                       )
       result_log_scan_2 = ResultLogScan(scan_type='md5',
                                         scan_value='foobar',
                                         reputations={}
                                         )
       settings = Settings(name='virustotal_min_match_count',
                           setting=1,
                           created_at=dt.datetime.now())

       av_engines_1 = VirusTotalAvEngines(name='boo', status=True)
       av_engines_2 = VirusTotalAvEngines(name='baz', status=False)
       vt = ThreatIntelCredentials(
           intel_name='virustotal',
           credentials={"key": "foo"}
       )
       db.session.add(vt)
       db.session.add(result_log_scan_1)
       db.session.add(result_log_scan_2)
       db.session.add(settings)
       db.session.add(av_engines_1)
       db.session.add(av_engines_2)
       resp = {'response_code': 200, 'results':[ {'positives': 1, 'resource': 'foo',
                                                 'scans': {'boo': {'detected': True}, 'baz': {'detected': False}}},
              {'positives': 1, 'resource': 'foobar',
               'scans': {'boo': {'detected': True}, 'baz': {'detected': False}}}]}
       with mock.patch("polylogyx.plugins.intel.virustotal.VirusTotalPublicApi.get_file_report",
                       return_value=resp) as pmock:
           vt = VTIntel(self.config)
           vt.update_credentials()
           vt.analyse_pending_hashes()
       assert pmock.called
       assert result_log_scan_1.reputations['virustotal_detected'] is True
       assert result_log_scan_2.reputations['virustotal_detected'] is True

   def test_vt_detection_with_lower_match_count(self, db):

       result_log_scan = ResultLogScan(scan_type='md5',
                                       scan_value='foo',
                                       reputations={}
                                       )
       settings= Settings(name='virustotal_min_match_count',
                          setting=1,
                          created_at=dt.datetime.now())

       av_engines_1= VirusTotalAvEngines(name='boo',status=False)
       av_engines_2= VirusTotalAvEngines(name='baz',status=False)
       av_engines_3 = VirusTotalAvEngines(name='xyz', status=False)
       vt = ThreatIntelCredentials(
           intel_name='virustotal',
           credentials={"key": "foo"}
       )
       db.session.add(vt)
       db.session.add(result_log_scan)
       db.session.add(settings)
       db.session.add(av_engines_1)
       db.session.add(av_engines_2)
       db.session.add(av_engines_3)
       resp={'response_code':200,'results':{'positives':1,'resource':'foo','scans':{'boo':{'detected':True},'baz':{'detected':False},
                                                                                    'abc':{'detected':True}}}}
       with mock.patch("polylogyx.plugins.intel.virustotal.VirusTotalPublicApi.get_file_report", return_value=resp) as pmock:
           vt = VTIntel(self.config)
           vt.update_credentials()
           vt.analyse_pending_hashes()
       assert pmock.called
       assert result_log_scan.reputations['virustotal_detected'] is True

   def test_vt_detection_with_higher_match_count(self, db):
       result_log_scan = ResultLogScan(scan_type='md5',
                                       scan_value='foo',
                                       reputations={}
                                       )
       settings = Settings(name='virustotal_min_match_count',
                           setting=3,
                           created_at=dt.datetime.now())

       av_engines_1 = VirusTotalAvEngines(name='boo', status=False)
       av_engines_2 = VirusTotalAvEngines(name='baz', status=False)
       av_engines_3 = VirusTotalAvEngines(name='xyz', status=False)
       vt = ThreatIntelCredentials(
           intel_name='virustotal',
           credentials={"key": "foo"}
       )
       db.session.add(vt)
       db.session.add(result_log_scan)
       db.session.add(settings)
       db.session.add(av_engines_1)
       db.session.add(av_engines_2)
       db.session.add(av_engines_3)
       resp = {'response_code': 200, 'results': {'positives': 2, 'resource': 'foo',
                                                 'scans': {'boo': {'detected': True}, 'baz': {'detected': False},
                                                           'abc': {'detected': True}}}}
       with mock.patch("polylogyx.plugins.intel.virustotal.VirusTotalPublicApi.get_file_report",
                       return_value=resp) as pmock:
           vt = VTIntel(self.config)
           vt.update_credentials()
           vt.analyse_pending_hashes()
       assert pmock.called
       assert result_log_scan.reputations['virustotal_detected'] is False

   def test_vt_detection_with_higher_match_count_and_one_enabled_av_engine(self, db):
       result_log_scan = ResultLogScan(scan_type='md5',
                                       scan_value='foo',
                                       reputations={}
                                       )
       settings = Settings(name='virustotal_min_match_count',
                           setting=3,
                           created_at=dt.datetime.now())

       av_engines_1 = VirusTotalAvEngines(name='boo', status=True)
       av_engines_2 = VirusTotalAvEngines(name='baz', status=False)
       av_engines_2 = VirusTotalAvEngines(name='xyz', status=False)
       vt = ThreatIntelCredentials(
           intel_name='virustotal',
           credentials={"key": "foo"}
       )
       db.session.add(vt)
       db.session.add(result_log_scan)
       db.session.add(settings)
       db.session.add(av_engines_1)
       db.session.add(av_engines_2)
       resp = {'response_code': 200, 'results': {'positives': 2, 'resource': 'foo',
                                                 'scans': {'boo': {'detected': True}, 'baz': {'detected': False},
                                                           'abc': {'detected': True}}}}
       with mock.patch("polylogyx.plugins.intel.virustotal.VirusTotalPublicApi.get_file_report",
                       return_value=resp) as pmock:
           vt = VTIntel(self.config)
           vt.update_credentials()
           vt.analyse_pending_hashes()
       assert pmock.called
       assert result_log_scan.reputations['virustotal_detected'] is True

   def test_vt_genearte_alerts(self,db,node):
       result_log = ResultLog(
           name='dummy',
           node= node,
           uuid='foobar',
           timestamp=dt.datetime.utcnow(),
           columns={'md5':'foo'}
       )
       result_log_scan = ResultLogScan(scan_type='md5',
                                       scan_value='foo',
                                       reputations={'virustotal': {'scans': {'abc': {'detected': True},
                                                    'baz': {'detected': False}, 'boo': {'detected': True}},
                                                    'resource': 'foo', 'positives': 2}, 'virustotal_detected': True}

                                       )
       db.session.add(result_log)
       db.session.add(result_log_scan)
       result_log_scan.result_logs.append(result_log)
       db.session.commit()
       vt = VTIntel(self.config)
       with mock.patch('polylogyx.utils.intel.send_alert') as pmock:
            vt.generate_alerts()
       alert=Alerts.query.all()[0]
       assert pmock.called
       assert alert.source == 'virustotal'
       assert alert.source_data == result_log_scan.reputations['virustotal']
       assert alert.node_id == node.id




