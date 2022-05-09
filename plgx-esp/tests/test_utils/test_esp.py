from polylogyx.utils import esp
from polylogyx.db.models import NodeConfig
from flask import current_app
import pytest
data = {
                "enroll_secret": "secret",
                "host_identifier": "foobar",
                "platform_type": "9",
                "host_details": {
                    "os_version": {
                    "_id": "20.04",
                    "arch": "x86_64",
                    "codename": "focal",
                    "major": "20",
                    "minor": "04",
                    "name": "Ubuntu",
                    "patch": "0",
                    "pid_with_namespace": "0",
                    "platform": "ubuntu",
                    "platform_like": "debian",
                    "version": "20.04.3 LTS (Focal Fossa)"
                    },
                    "osquery_info": {
                    "build_distro": "centos7",
                    "build_platform": "linux",
                    "config_hash": "",
                    "config_valid": "0",
                    "extensions": "active",
                    "instance_id": "da67c296-796c-4bba-aae8-8c4a060e8470",
                    "pid": "34140",
                    "platform_mask": "9",
                    "start_time": "1633957815",
                    "uuid": "3f0e144c-1f0c-11b2-a85c-ffcce65db30c",
                    "version": "5.0.1",
                    "watcher": "34133"
                    },
                    "platform_info": {
                    "address": "0xe000",
                    "date": "06/29/2020",
                    "extra": "",
                    "revision": "1.21",
                    "size": "16777216",
                    "vendor": "LENOVO",
                    "version": "R0ZET43W (1.21 )",
                    "volume_size": "0"
                    },
                    "system_info": {
                    "board_model": "20Q6S7WM00",
                    "board_serial": "L1HF05T02HE",
                    "board_vendor": "LENOVO",
                    "board_version": "SDK0J40697 WIN",
                    "computer_name": "",
                    "cpu_logical_cores": "8",
                    "cpu_microcode": "0xea",
                    "cpu_physical_cores": "4",
                    "cpu_subtype": "142",
                    "cpu_type": "x86_64",
                    "hardware_model": "20Q6S7WM00",
                    "hardware_serial": "PF279TD9",
                    "hardware_vendor": "LENOVO",
                    "hardware_version": "ThinkPad L490",
                    "hostname": "Prasnath",
                    "local_hostname": "Prasanth",
                    "physical_memory": "16418652160",
                    "uuid": "3f0e144c-1f0c-11b2-a85c-ffcce65db30c"
                    }
                }
                }
class Testesp:
    def test_update_mac_address(self,node):
        mac_add = {"mac_address":"Test"}
        esp.update_mac_address(node,mac_add)
        assert node.network_info == mac_add 

    def test_update_system_info(self,node):
        sys_info = {"mac":"Test"}
        esp.update_system_info(node,sys_info) 
        assert node.node_info["mac"] == "Test"
    
    def test_update_system_info_no_capture_info(self,node):
        sys_info = {"mac":"Test"}
        current_app.config["POLYLOGYX_CAPTURE_NODE_INFO"]=[]
        assert esp.update_system_info(node,sys_info) is None

    def test_update_system_info_no_node_info(self,node):
        sys_info = {"mac":"Test"}
        node.node_info = None
        esp.update_system_info(node,sys_info) 
        assert node.node_info is not None

    def test_update_os_info(self,node):
        os_info = {"mac":"Test"}
        esp.update_os_info(node,os_info) 
        assert node.os_info==os_info

    def test_osquery_info(self,node):
        os_info = {"version":"5.0"}
        esp.update_osquery_info(node,os_info) 
        assert node.host_details["osquery_version"]=="5.0"

    def test_fetch_system_info(self):
        assert esp.fetch_system_info({"system_info":"Test"})=="Test"

    def test_fetch_platform(self):
        assert esp.fetch_platform({"os_version":{"platform":"linux"}}) == "linux"

    def test_update_system_details(self,node):
        esp.update_system_details(data,node)
        assert node.host_details["osquery_version"] == "5.0.1"

    def test_assign_config_on_enroll(self,node):
        esp.assign_config_on_enroll(data,node)
        assert NodeConfig.query.filter(NodeConfig.node_id ==node.id).count()==1
        data["host_details"]["system_info"].pop("computer_name")
        esp.assign_config_on_enroll(data,node)
        assert NodeConfig.query.filter(NodeConfig.node_id ==node.id).count()==1
        

    def test_parse_config_conditions(self):
        hname = "foobar"
        os_name = "linux"
        assert esp.parse_config_conditions({},hname,os_name) == False
        assert esp.parse_config_conditions({"hostname":{"value":"foobar"},"os_name":{"value":"linux"}},hname,os_name) == True


#29-30, 43, 46, 54-55, 90, 
#92, 136-137, 146-147, 152