from flask import url_for


class TestLogSetting:
    def test_log_setting(self, db, testapp):
        resp = testapp.put_json(
            url_for("api.log_setting"),
            params={"log_level": "ERROR", "host": "localhost"},
            extra_environ=dict(REMOTE_ADDR="127.0.0.1"),
            expect_errors=True,
        )
        assert resp.json["status"] == "success"
