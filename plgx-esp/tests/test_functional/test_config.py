# -*- coding: utf-8 -*-
from flask import url_for

from polylogyx.db.models import FilePath, Pack, Query, Tag

from ..factories import PackFactory, QueryFactory, TagFactory


class TestConfiguration:
    def test_bad_post_request(self, node, testapp):
        resp = testapp.post(
            url_for("api.configuration"), {"foo": "bar"}, expect_errors=True
        )
        assert not resp.normal_body

    def test_missing_node_key(self, node, testapp):
        resp = testapp.post_json(
            url_for("api.configuration"), {"foo": "bar"}, expect_errors=True
        )
        assert not resp.normal_body
        # assert resp.json == {'node_invalid': True}

    def test_invalid_node_key(self, node, testapp):
        resp = testapp.post_json(
            url_for("api.configuration"), {"node_key": "invalid"}, expect_errors=True
        )
        assert resp.json == {"node_invalid": True}

    def test_valid_node_key(self, node, testapp):
        resp = testapp.post_json(
            url_for("api.configuration"),
            {"node_key": node.node_key},
            expect_errors=True,
        )
        assert resp.json["node_invalid"] is False

    def test_inactive_node_key(self, node, testapp):
        node.is_active = False
        node.save()
        resp = testapp.post_json(
            url_for("api.configuration"),
            {"node_key": node.node_key},
            expect_errors=True,
        )
        assert resp.json["node_invalid"] is False

    def test_configuration_has_all_required_values(self, node, testapp):
        tag = TagFactory(value="foobar")
        tag2 = TagFactory(value="barbaz")
        pack = PackFactory(name="foobar")
        pack.tags.append(tag)

        sql = "select * from foobar;"
        query = QueryFactory(name="foobar", sql=sql)
        query2 = QueryFactory(name="barbaz", sql=sql)
        query3 = QueryFactory(name="barfoo", sql=sql)
        query.tags.append(tag)
        query.save()

        pack.queries.append(query)
        pack.save()

        node.tags.append(tag)
        node.save()

        pack2 = PackFactory(name="barbaz")
        pack2.tags.append(tag2)
        pack2.queries.append(query)
        pack2.queries.append(query2)
        pack2.save()

        resp = testapp.post_json(
            url_for("api.configuration"),
            {"node_key": node.node_key},
            expect_errors=True,
        )

        assert resp.json["node_invalid"] is False

        assert pack.name in resp.json["packs"]
        assert list(resp.json["packs"].keys()) == [pack.name]  # should be the only key

        assert query.name in resp.json["packs"][pack.name]["queries"]
        assert list(resp.json["packs"][pack.name]["queries"].keys()) == [query.name]

        # should default to 'removed': true
        assert resp.json["packs"][pack.name]["queries"][query.name]["query"] == sql
        assert resp.json["packs"][pack.name]["queries"][query.name]["removed"] == False

        assert "schedule" in resp.json

    def test_configuration_will_respect_removed_false(self, node, testapp):
        tag = TagFactory(value="foobar")
        pack = PackFactory(name="foobar")
        pack.tags.append(tag)

        sql = "select * from foobar;"
        query = QueryFactory(name="foobar", sql=sql, removed=False)
        pack.queries.append(query)
        pack.save()
        node.tags.append(tag)
        node.save()

        resp = testapp.post_json(
            url_for("api.configuration"),
            {"node_key": node.node_key},
            expect_errors=True,
        )

        # as above, but 'removed': false
        assert resp.json["packs"][pack.name]["queries"][query.name]["query"] == sql
        assert resp.json["packs"][pack.name]["queries"][query.name]["removed"] is False

    def test_valid_configuration(self, node, testapp):
        resp = testapp.post_json(
            url_for("api.configuration"),
            {"node_key": node.node_key},
            expect_errors=True,
        )

        assert resp.json["node_invalid"] is False

        first_config = resp.json
        first_config.pop("node_invalid")
        
        assert first_config == node.get_config()

        tag = Tag.create(value="foo")
        node.tags.append(tag)
        node.save()

        # test adding a tag to a query results in the query being included
        # for this configuration

        query1 = Query.create(name="bar", sql="select * from osquery_info;")
        query2 = Query.create(name="foobar", sql="select * from system_info;")
        query2.tags.append(tag)
        query2.save()

        # test adding a tag to a pack results in the pack being included
        # for this configuration

        pack = Pack.create(name="baz")
        pack.queries.append(query1)
        pack.tags.append(tag)
        pack.save()

        file_path = FilePath.create(
            category="foobar",
            target_paths=[
                "/home/foobar/%%",
            ],
        )
        file_path.tags.append(tag)
        file_path.save()

        resp = testapp.post_json(
            url_for("api.configuration"),
            {"node_key": node.node_key},
            expect_errors=True,
        )

        assert resp.json["node_invalid"] is False

        second_config = resp.json
        second_config.pop("node_invalid")

        assert second_config != first_config
        assert second_config == node.get_config()

    def test_adding_and_then_removing_results_in_valid_configuration(
        self, node, testapp
    ):

        tag = Tag.create(value="foo")
        node.tags.append(tag)

        assert not node.get_config()["packs"]  # should be an empty {}
        assert not node.get_config()["schedule"]  # should be an empty {}

        query = Query.create(name="foobar", sql="select * from osquery_info;")
        query.tags.append(tag)
        query.save()

        assert node.get_config()["schedule"]
        assert query.name in node.get_config()["schedule"]
        assert not node.get_config()["packs"]  # should be an empty {}
