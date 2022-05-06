# -*- coding: utf-8 -*-

from flask import url_for

from polylogyx.db.models import Node, Tag

from ..factories import NodeFactory, TagFactory


class TestEnrolling:
    def test_bad_post_request(self, node, testapp):

        resp = testapp.post_json(
            url_for("api.enroll"),
            params={"host_identifier": node.host_identifier},
            extra_environ=dict(REMOTE_ADDR="127.0.0.2"),
            expect_errors=True,
        )

        assert resp.json == {"node_invalid": True}

    def test_missing_enroll_secret(self, node, testapp):
        resp = testapp.post_json(
            url_for("api.enroll"),
            params={"host_identifier": node.host_identifier},
            extra_environ=dict(REMOTE_ADDR="127.0.0.2"),
            expect_errors=True,
        )
        assert resp.json == {"node_invalid": True}

    def test_invalid_enroll_secret(self, node, testapp):
        resp = testapp.post_json(
            url_for("api.enroll"),
            params={
                "enroll_secret": "badsecret",
                "host_identifier": node.host_identifier,
            },
            expect_errors=True,
        )
        assert resp.json == {"node_invalid": True}

    def test_valid_enroll_secret(self, db, testapp):

        enroll_secret = testapp.app.config["POLYLOGYX_ENROLL_SECRET"][0]
        resp = testapp.post_json(
            url_for("api.enroll"),
            params={"enroll_secret": enroll_secret, "host_identifier": "foobaz"},
            extra_environ=dict(REMOTE_ADDR="127.0.0.2"),
            expect_errors=True,
        )
        assert resp.json["node_invalid"] is False
        assert resp.json["node_key"]
        n = Node.query.filter_by(node_key=resp.json["node_key"]).one()
        assert n.node_is_active()
        assert n.last_ip == "127.0.0.2"

    def test_valid_reenrollment(self, node, testapp):
        resp = testapp.post_json(
            url_for("api.enroll"),
            params={
                "enroll_secret": node.enroll_secret,
                "host_identifier": node.host_identifier,
            },
            extra_environ=dict(REMOTE_ADDR="127.0.0.2"),
            expect_errors=True,
        )

        assert resp.json["node_invalid"] is False
        assert resp.json["node_key"] == node.node_key
        assert node.node_is_active()
        assert node.last_ip == "127.0.0.2"

    def test_duplicate_host_identifier_when_expecting_unique_ids(self, node, testapp):
        # When the application is configured POLYLOGYX_EXPECTS_UNIQUE_HOST_ID = True
        # then we're responsible for ensuring host_identifiers are unique.
        # In osquery, this requires running osquery with the
        # `--host_identifier=uuid` command-line flag. Otherwise, there is
        # a possibility that more than one node will have the same hostname.

        testapp.app.config["POLYLOGYX_EXPECTS_UNIQUE_HOST_ID"] = True

        enroll_secret = testapp.app.config["POLYLOGYX_ENROLL_SECRET"][0]

        existing = NodeFactory(host_identifier="foo")

        resp = testapp.post_json(
            url_for("api.enroll"),
            params={
                "enroll_secret": enroll_secret,
                "host_identifier": existing.host_identifier,
            },
            extra_environ=dict(REMOTE_ADDR="127.0.0.2"),
            expect_errors=True,
        )

        assert resp.json["node_invalid"] is False
        assert resp.json["node_key"] == existing.node_key
        assert existing.node_is_active()
        assert existing.last_ip == "127.0.0.2"
        assert node.last_ip != "127.0.0.2"

    def test_default_tags_that_dont_exist_yet_are_created(self, db, testapp):
        testapp.app.config["POLYLOGYX_ENROLL_DEFAULT_TAGS"] = ["foo", "bar"]
        enroll_secret = testapp.app.config["POLYLOGYX_ENROLL_SECRET"][0]

        node = Node.query.filter_by(host_identifier="kungfoo").first()

        assert not node
        assert not Tag.query.all()

        resp = testapp.post_json(
            url_for("api.enroll"),
            params={
                "enroll_secret": enroll_secret,
                "host_identifier": "kungfoo",
            },
            expect_errors=True,
        )

        node = Node.query.filter_by(host_identifier="kungfoo").first()
        assert node
        assert node.tags

        t1 = Tag.query.filter_by(value="foo").first()
        t2 = Tag.query.filter_by(value="bar").first()

        assert t1 in node.tags
        assert t2 in node.tags

    def test_default_tags_that_exit_are_added(self, db, testapp):
        testapp.app.config["POLYLOGYX_ENROLL_DEFAULT_TAGS"] = ["foobar"]
        enroll_secret = testapp.app.config["POLYLOGYX_ENROLL_SECRET"][0]

        tag = TagFactory(value="foobar")

        node = Node.query.filter_by(host_identifier="kungfoo").first()
        assert not node

        resp = testapp.post_json(
            url_for("api.enroll"),
            params={"enroll_secret": enroll_secret, "host_identifier": "kungfoo"},
            extra_environ=dict(REMOTE_ADDR="127.0.0.2"),
            expect_errors=True,
        )

        node = Node.query.filter_by(host_identifier="kungfoo").first()
        assert node
        assert node.tags
        assert tag in node.tags
        assert node.node_is_active()
        assert node.last_ip == "127.0.0.2"

    def test_reenrolling_node_does_not_get_new_tags(self, db, node, testapp):
        testapp.app.config["POLYLOGYX_ENROLL_DEFAULT_TAGS"] = ["foo", "bar"]
        enroll_secret = testapp.app.config["POLYLOGYX_ENROLL_SECRET"][0]

        tag = TagFactory(value="foobar")
        tag.save()
        node.tags.append(tag)
        node.last_ip = "127.0.0.1"

        resp = testapp.post_json(
            url_for("api.enroll"),
            params={
                "enroll_secret": enroll_secret,
                "host_identifier": node.host_identifier,
            },
            extra_environ=dict(REMOTE_ADDR="127.0.0.2"),
            expect_errors=True,
        )

        assert Tag.query.count() == 1
        assert node.tags == [tag]
        assert node.node_is_active()
        assert node.last_ip == "127.0.0.2"

    def test_enroll_secret_tags(self, db, node, testapp):
        testapp.app.config["POLYLOGYX_ENROLL_SECRET_TAG_DELIMITER"] = ":"
        testapp.app.config["POLYLOGYX_EXPECTS_UNIQUE_HOST_ID"] = True
        enroll_secret = testapp.app.config["POLYLOGYX_ENROLL_SECRET"][0]
        resp = testapp.post_json(
            url_for("api.enroll"),
            params={"enroll_secret": enroll_secret, "host_identifier": "foobaz"},
            extra_environ=dict(REMOTE_ADDR="127.0.0.2"),
            expect_errors=True,
        )

        assert resp.json["node_invalid"] is False
        assert resp.json["node_key"] != node.node_key

        n = Node.query.filter_by(node_key=resp.json["node_key"]).one()
        assert n.node_is_active()
        assert n.last_ip == "127.0.0.2"
        assert not n.tags

        resp = testapp.post_json(
            url_for("api.enroll"),
            params={
                "enroll_secret": ":".join([enroll_secret, "foo", "bar"]),
                "host_identifier": "barbaz",
            },
            extra_environ=dict(REMOTE_ADDR="127.0.0.2"),
            expect_errors=True,
        )

        assert resp.json["node_invalid"] is False
        assert resp.json["node_key"] != node.node_key

        n = Node.query.filter_by(node_key=resp.json["node_key"]).one()
        assert n.node_is_active()
        assert n.last_ip == "127.0.0.2"
        assert len(n.tags) == 2
        assert "foo" in (t.value for t in n.tags)
        assert "bar" in (t.value for t in n.tags)

        resp = testapp.post_json(
            url_for("api.enroll"),
            params={
                "enroll_secret": ":".join([enroll_secret, "foo", "bar", "baz"]),
                "host_identifier": "barbaz",
            },
            extra_environ=dict(REMOTE_ADDR="127.0.0.2"),
            expect_errors=True,
        )
        assert resp.json["node_key"] != node.node_key
        assert resp.json["node_key"] == n.node_key

        n = Node.query.filter_by(node_key=resp.json["node_key"]).one()
        assert n.node_is_active()
        assert n.last_ip == "127.0.0.2"
        assert len(n.tags) == 2
        assert "foo" in (t.value for t in n.tags)
        assert "bar" in (t.value for t in n.tags)

        testapp.app.config["POLYLOGYX_ENROLL_SECRET"].append(":".join(enroll_secret))
        testapp.app.config["POLYLOGYX_ENROLL_SECRET_TAG_DELIMITER"] = ","
        resp = testapp.post_json(
            url_for("api.enroll"),
            {"enroll_secret": ":".join(enroll_secret), "host_identifier": "bartab"},
            expect_errors=True,
            extra_environ=dict(REMOTE_ADDR="127.0.0.2"),
        )

        assert resp.json["node_invalid"] is False
        assert resp.json["node_key"] != node.node_key

        n = Node.query.filter_by(node_key=resp.json["node_key"]).one()
        assert n.node_is_active()
        assert n.last_ip == "127.0.0.2"
        assert not n.tags

    def test_enroll_max_secret_tags(self, db, node, testapp):
        testapp.app.config["POLYLOGYX_ENROLL_SECRET_TAG_DELIMITER"] = ":"
        testapp.app.config["POLYLOGYX_EXPECTS_UNIQUE_HOST_ID"] = True
        enroll_secret = testapp.app.config["POLYLOGYX_ENROLL_SECRET"][0]
        enroll_secret = ":".join([enroll_secret] + list("abcdef1234567890"))
        resp = testapp.post_json(
            url_for("api.enroll"),
            {
                "enroll_secret": ":".join(
                    [
                        enroll_secret,
                        "foo",
                    ]
                ),
                "host_identifier": "barbaz",
            },
            extra_environ=dict(REMOTE_ADDR="127.0.0.2"),
            expect_errors=True,
        )

        assert resp.json["node_invalid"] is False
        assert resp.json["node_key"] != node.node_key

        n = Node.query.filter_by(node_key=resp.json["node_key"]).one()
        assert n.node_is_active()
        assert n.last_ip == "127.0.0.2"
        assert len(n.tags) == 10  # max 10 tags when passing tags w/enroll secret
