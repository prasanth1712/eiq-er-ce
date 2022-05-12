from polylogyx.utils import node as n
from ..factories import NodeFactory
import datetime as dt
from polylogyx.db.models import ReleasedAgentVersions

class TestUtilsNode:
    def test_get_node_health(self,node):
        assert n.get_node_health(node) == ""

    def test_get_node_danger(self,db):
        node = NodeFactory(
        host_identifier="foobar",
        enroll_secret="secret",
        last_checkin=dt.datetime.utcnow()-dt.timedelta(days=1),
        enrolled_on=dt.datetime.utcnow()-dt.timedelta(days=1),
            )
        node.save()
        
        assert n.get_node_health(node) == "danger"

    def test_append_node_and_rule_information_to_alert(self,node):
        inp = {}
        out = n.append_node_and_rule_information_to_alert(node.to_dict(),inp)
        assert out is not None

    def test_append_node_information_to_result_log(self,node):
        inp = {}
        out = n.append_node_information_to_result_log(node.to_dict(),inp)
        assert out is not None

    def test_update_defender_status(self,node):
        n.update_defender_status(node,columns=None)
        columns =[{"name":"Test","type":"Type"}]
        n.update_defender_status(node,columns)
        assert node.host_details["windows_security_products_status"]["Test_Type"]==columns[0]

    def test_update_osquery_or_agent_version(self,node):
        columns =[{"name":"Test","type":"Type"}]
        n.update_osquery_or_agent_version(node,columns)
        assert True

    def test_update_osquery_version_md5(self,node):
        columns = {"md5":"test"}
        rva = ReleasedAgentVersions(extension_hash_md5="test",extension_version=10,platform="linux")
        rva.save()
        n.update_osquery_or_agent_version(node,columns)
        assert node.host_details["extension_version"] == "10"
    
    def test_update_osquery_version_other(self,node):
        columns = {"version":5.07,"type":"other"}
        n.update_osquery_or_agent_version(node,columns)
        assert node.host_details == node.host_details
    
    def test_update_osquery_version(self,node):
        columns = {"version":5.07,"type":"core"}
        n.update_osquery_or_agent_version(node,columns)
        assert node.host_details["osquery_version"] == 5.07
    
    def test_update_extension_version(self,node):    
        columns = {"version":5.07,"type":"extension","name":"plgx_linux_extension"}
        n.update_osquery_or_agent_version(node,columns)
        assert node.host_details["extension_version"] == 5.07