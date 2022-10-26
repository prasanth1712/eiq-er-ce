from datetime import datetime
from typing import Set
import pytest
import manage as mng
from flask import current_app
import pathlib
from polylogyx.db.models import DefaultFilters,DefaultQuery,ResultLogScan,Rule,VirusTotalAvEngines, Settings
from polylogyx.db.models import ResultLog,User


app_path = pathlib.Path(current_app.root_path)
class TestManage:
    def test_add_default_filters(self,db):
        import os
        file_path =pathlib.Path.joinpath(app_path.parent,"default_data/default_filters/default_filter_linux.conf")
        mng.add_default_filters(file_path.as_posix(), "linux", "Default", True)
        assert DefaultFilters.query.count() > 0

    def test_add_default_queries(self,db):
        file_path =pathlib.Path.joinpath(app_path.parent,"default_data/default_queries/default_queries_linux.conf")
        mng.add_default_queries(file_path.as_posix(), "linux", "Default", True)
        assert DefaultQuery.query.count() > 0

    def test_add_default_queries_update(self,db):
        file_path =pathlib.Path.joinpath(app_path.parent,"default_data/default_queries/default_queries_linux.conf")
        mng.add_default_queries(file_path.as_posix(),"linux","Default",True)
        before_cnt = DefaultQuery.query.count()
        mng.add_default_queries(file_path.as_posix(),"linux","Default",False)
        after_cnt = DefaultQuery.query.count()
        assert before_cnt == after_cnt

    def test_add_default_queries_exception(self):
        with pytest.raises(Exception) as e:
            mng.add_default_queries(None,"linux","Default",False)

    def test_add_rules(self,db):
        file_path =pathlib.Path.joinpath(app_path.parent,"default_data/mitre-attack/at_command.json")
        mng.add_rules(file_path.as_posix())
        assert Rule.query.count() > 0
        
    def test_add_rules_existing(self,db):
        file_path =pathlib.Path.joinpath(app_path.parent,"default_data/mitre-attack/at_command.json")
        mng.add_rules(file_path.as_posix())
        cnt = Rule.query.count()
        mng.add_rules(file_path.as_posix())
        assert Rule.query.count() == cnt

    def test_add_default_vt_av_engines(self,db):
        file_path =pathlib.Path.joinpath(app_path.parent,"default_data/Virustotal-avengines/default_VT_Av_engines.json")
        mng.add_default_vt_av_engines(file_path.as_posix())
        assert VirusTotalAvEngines.query.count()>0

    def test_add_default_vt_av_engines_exception(self):
        mng.add_default_vt_av_engines("some-unknown-filepath")
        assert True
    
    def test_update_vt_match_count(self,db):
        mng.update_vt_match_count(10)
        assert Settings.query.count()>0

    def test_update_settings(self,db):
        mng.update_settings(data_retention_days=10,alert_aggregation_duration=20)
        pdd = Settings.query.filter(Settings.name=="data_retention_days").first()
        agd = Settings.query.filter(Settings.name=="alert_aggregation_duration").first()
        assert pdd.setting == '10'
        assert agd.setting == '20'

    # def test_add_result_log_map_data(self,node):
    #     rls = ResultLogScan(scan_type="test", scan_value="test", reputations={})
    #     rl = ResultLog("Test",columns={"test":"test"},node=node)
    #     rls.save()
    #     rl.save()
    #     mng.add_result_log_map_data()
    #     assert rls.result_logs is not None

    def test_update_osquery_schema(self,db):
        file_path =pathlib.Path.joinpath(app_path.parent,"polylogyx/resources/osquery_schema.json")
        with pytest.raises(SystemExit) as e:
            mng.update_osquery_schema(file_path=file_path.as_posix())
        assert e.value.code == 0

    def test_update_osquery_schema_invalid_file(self,db):
        file_path =pathlib.Path.joinpath(app_path.parent,"polylogyx/resources/test.json")
        with pytest.raises(SystemExit) as e:
            mng.update_osquery_schema(file_path=file_path.as_posix())
        assert e.value.code == 0


    def test_update_user_invalid_username(self,db):
        with pytest.raises(SystemExit) as e:
            mng.update_user(username="Test",password="Test",email="Test")
        assert e.value.code == 1

    def test_update_user_valid_username(self,db):
        u=User(username="Test",password="Test",email="test",first_name="Test",last_name="Test")
        u.save()
        with pytest.raises(SystemExit) as e:
            mng.update_user(username="Test",password="Test",email="test")
        assert e.value.code == 0

    def test_delete_existing_unmapped_queries_filters(self,db):
        # Commented will not work as config id cannot be null
        # df = DefaultFilters(filters="Test", "linux", created_at=datetime.utcnow())
        # df.save()

        dq = DefaultQuery("Test",sql="Test")
        dq.save()
        mng.delete_existing_unmapped_queries_filters()
        assert DefaultFilters.query.count()==0
        assert DefaultQuery.query.count()==0