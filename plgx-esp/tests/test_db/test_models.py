# -*- coding: utf-8 -*-
import datetime as dt

import pytest

from polylogyx.db.models import Config, FilePath, VirusTotalAvEngines, NodeConfig, Pack, Query, Tag

from ..factories import AlertFactory, NodeFactory, PackFactory, QueryFactory, TagFactory


@pytest.mark.usefixtures("db")
class TestNode:
    def test_factory(self, db):
        node = NodeFactory(host_identifier="foo")
        db.session.commit()
        assert node.node_key is not None
        assert node.host_identifier == "foo"

    def test_tags(self):
        tag = Tag.create(value="foo")
        node = NodeFactory(host_identifier="foo")
        node.tags.append(tag)
        node.save()
        assert tag in node.tags
        assert tag.nodes_count > 0

    def test_config(self,node):

        tag = Tag.create(value="foo")
        node.tags.append(tag)
        node.save()

        query1 = Query.create(name="bar", sql="select * from osquery_info;")
        query2 = Query.create(name="foobar", sql="select * from system_info;")
        query2.tags.append(tag)
        query2.save()

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

        assert tag.packs_count > 0
        assert tag.queries_count > 0  
        assert tag.file_paths_count > 0
        assert tag in pack.tags
        assert tag in query2.tags
        assert tag in file_path.tags
        assert tag not in query1.tags
        assert query1 in pack.queries
        assert query2 not in pack.queries

        assert pack in node.packs
        assert query2 in node.queries
        assert query1 not in node.queries

        config = node.get_config()

        assert pack.name in config["packs"]
        assert query1.name in config["packs"][pack.name]["queries"]
        assert query1.sql == config["packs"][pack.name]["queries"][query1.name]["query"]

        assert query2.name not in config["packs"]
        assert query2.name in config["schedule"]
        assert query2.sql == config["schedule"][query2.name]["query"]

        # assert file_path.category in config["file_paths"]


@pytest.mark.usefixtures("db")
class TestQuery:
    def test_factory(self, db):
        query = QueryFactory(name="foobar", query="select * from foobar;")
        db.session.commit()

        assert query.name == "foobar"
        assert query.sql == "select * from foobar;"


@pytest.mark.usefixtures("db")
class TestFilePath:
    def test_create(self):
        target_paths = [
            "/root/.ssh/%%",
            "/home/.ssh/%%",
        ]

        file_path = FilePath.create(category="foobar", target_paths=target_paths)
        assert file_path.to_dict() == {"foobar": target_paths}

    def test_update(self):
        target_paths = [
            "/root/.ssh/%%",
            "/home/.ssh/%%",
        ]

        file_path = FilePath.create(category="foobar", target_paths=target_paths)
        assert file_path.to_dict() == {"foobar": target_paths}

        target_paths.append("/etc/%%")
        file_path.set_paths(*target_paths)
        file_path.save()
        assert file_path.to_dict() == {"foobar": target_paths}


class TestVirusTotalAVEngine:

    def test_init(self,db):
        vte = VirusTotalAvEngines(name="Test",status="Test",description="Test")
        assert vte.name == "Test"
        assert vte.status == "Test"
        assert vte.description == "Test"


from polylogyx.db.models import DefaultQuery
class TestDefaultQuery:

    def test_init(self,db):
        dfq = DefaultQuery(name="Test")
        assert dfq.name == "Test"

    def test_init(self,db):
        dfq = DefaultQuery(name="Test",query="select version()")
        dfq.save()
        dict = dfq.to_dict()
        assert dict["query"] == "select version()"

from polylogyx.db.models import DefaultFilters
from datetime import datetime as dt
class TestDefaultFilters:

    def test_init(self,db):
        df = DefaultFilters(filters="{}",platform="linux",created_at=dt.utcnow(),type="")
        assert df.serialize["platform"] == "linux"


from polylogyx.db.models import ResultLog
class TestResultLog:

    def test_init(self,node):
        rl = ResultLog(name="Test",node=node)
        assert rl.node == node
        rl = ResultLog(name="Test",node_id=node.id,timestamp=dt.utcnow())
        assert rl.node_id == node.id
        assert rl.as_dict()["name"] == "Test"
        assert rl.to_dict()["name"] == "Test"


from polylogyx.db.models import AlertLog
class TestAlertLog:

    def test_init(self,node):
        al = AlertLog(name="Test",timestamp=dt.utcnow())
        assert al.name == "Test"
        assert al.to_dict()["name"] == "Test"

from polylogyx.db.models import DistributedQuery
class TestDistributedQuery:

    def test_init(self,node):
        dq = DistributedQuery(sql="Test")
        assert dq.sql == "Test"
        assert dq.to_dict()["sql"] == "Test"

from polylogyx.db.models import DistributedQueryResult
class TestDistributedQueryResult:

    def test_to_dict_obj(self,node):
        dqr = DistributedQueryResult(columns={"test":"test"})
        assert dqr.to_dict_obj()["columns"] == {"test":"test"}

from polylogyx.db.models import Rule
class TestRule:

    def test_to_dict(self,node):
        r = Rule(name="Test",alerters=["Email"])
        assert r.to_dict()["name"] == "Test"
        assert r.as_dict()["name"] == "Test"
        assert r.as_dict()["updated_at"] is not None

from polylogyx.db.models import User
class TestUser:

    def test_init(self,db):
        u = User(username="Test")
        assert u.username == "Test"
        u = User(username="Test",password="Test")
        assert u.password is not None
        
    def test_check_password(self,db):
        u = User(username="Test",password="Test")
        assert u.check_password("Test") == True

    def test_gen_auth_token(self,db):
        u = User(username="Test",password="Test")
        u.save()
        token = u.generate_auth_token()
        assert token
        assert User.verify_auth_token(token)==u

from polylogyx.db.models import Alerts
class TestAlerts:

    def test_to_dict(self,node):
        a = Alerts(message="Test",query_name="test",
        node_id=node.id,
        rule_id=None,
        recon_queries=None,
        result_log_uid=None,
        type=None,
        source=None,
        source_data=None,
        severity=None,)
        a.save()
        assert a.to_dict()["message"] == "Test"
        assert a.as_dict()["message"] == "Test"
        assert a.as_dict()["created_at"] is not None


from polylogyx.db.models import NodeData
class TestNodeData:

    def test_to_dict(self,node):
        n = NodeData(node=node,name="Test")
        assert n.name == "Test"
        assert n.to_dict()["name"] == "Test"
        assert n.to_dict_obj()["name"] == "Test"

from polylogyx.db.models import NodeReconData
class TestNodeReconData:

    def test_to_dict(self,db):
        n = NodeReconData(columns={},)
        assert n.to_dict()["columns"] == "{}"
        assert n.to_dict_obj()["columns"] == {}  

from polylogyx.db.models import CarveSession
class TestCarveSession:

    def test_init(self,node):
        n = CarveSession(node_id=node.id)
        assert n.node_id == node.id
        assert n.to_dict()["node_id"] == node.id


from polylogyx.db.models import ReleasedAgentVersions
class TestReleasedAgentVersions:

    def test_init(self,node):
        rav = ReleasedAgentVersions(platform="linux")
        assert rav.platform == "linux"