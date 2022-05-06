# -*- coding: utf-8 -*-
import pytest
from flask import url_for
from flask_login import current_user
from werkzeug.routing import BuildError

# from polylogyx.users.mixins import NoAuthUserMixin


class TestStandaloneApi:
    def test_no_manager(self, testapi, client):
        with pytest.raises(BuildError):
            url_for("manage.index")

        resp = client.get(url_for("api.index"))
        assert resp.status_code == 204

        resp = testapi.get("/pathdoesnotexist", expect_errors=True)
        assert resp.status_code == 404
