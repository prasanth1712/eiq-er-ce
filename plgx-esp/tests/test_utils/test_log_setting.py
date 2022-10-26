from polylogyx.utils.log_setting import _get_log_level_from_db,_check_log_level_exists,set_app_log_level,_set_log_level_to_db
from flask import current_app
from polylogyx.db.models import Settings

class TestUtilsLogSetting:

    def test_get_log_level_from_db(self,db):
        assert _get_log_level_from_db()=="WARNING"


    def test_get_log_level_from_db_no_setting(self,db):
        Settings.query.filter(
                    Settings.name == "er_log_level"
                ).delete()
        assert _get_log_level_from_db()=="WARNING"

    def test_check_log_level_exists(self,db):
        assert _check_log_level_exists() is None

    def test_set_log_level_to_db(self,db):
        _set_log_level_to_db("ERROR")
        assert _get_log_level_from_db()=="ERROR"

    def test_set_log_level_to_db_no_setting(self,db):
        Settings.query.filter(
                    Settings.name == "er_log_level"
                ).delete()
        _set_log_level_to_db("INFO")
        assert _get_log_level_from_db()=="INFO"


    def test_set_app_log_level(self,db):
        set_app_log_level("DEBUG")
        assert current_app.logger.level==10
