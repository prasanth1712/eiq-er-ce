from polylogyx.utils.cache import get_log_level,refresh_log_level
from flask import current_app
from polylogyx.utils.cache import redis_client
from polylogyx.db.models import Settings


class TestCache:

    def test_get_log_level(self, db):
        redis_client.delete('er_log_level')
        assert get_log_level() == current_app.config.get("POLYLOGYX_LOGGING_LEVEL","WARNING")
    
    def test_refresh_log_level(self,db):
        redis_client.set("er_log_level","DEBUG")
        refresh_log_level()
        assert get_log_level() == current_app.config.get("POLYLOGYX_LOGGING_LEVEL","WARNING")
