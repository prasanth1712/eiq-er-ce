from polylogyx.utils.cache import get_log_level,refresh_log_level
from flask import current_app
from polylogyx.extensions import cache

class TestCache:

    def test_get_log_level(self, db):
        assert get_log_level() == current_app.config.get("POLYLOGYX_LOGGING_LEVEL","WARNING")
    
    def test_refresh_log_level(self,db):
        cache.set("esp_log_level","DEBUG")
        refresh_log_level()
        assert get_log_level() == current_app.config.get("POLYLOGYX_LOGGING_LEVEL","WARNING")
