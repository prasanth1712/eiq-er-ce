import os

from polylogyx.plugins.intel.otx import OTXIntel
from polylogyx.db.models import ThreatIntelCredentials
from polylogyx.utils.otx.get_malicious import getValue, hostname, ip, url, file
from polylogyx.utils.otx.is_malicious import is_hash_malicious, is_file_malicious, is_ip_malicious, is_url_malicious, \
    is_host_malicious


class TestOTX:
    intel_name = "alienvault"
    safe_ip = '100.0.0.1'
    safe_host = 'foobar123.com'
    safe_domain = 'foobar123.com'
    safe_file_hash = '14758f1afd44c09b7992073ccf00b43d'  # md5sum of 'foobar'

    def test_init(self):
        otx_intel = OTXIntel(config={})
        assert otx_intel.name == self.intel_name
        assert otx_intel.LEVEL_MAPPINGS == OTXIntel.LEVEL_MAPPINGS

    def test_update_credentials(self, db):
        tic = ThreatIntelCredentials(intel_name=self.intel_name,
                                     credentials={'key': 'foo'})
        tic.save()
        otx_intel = OTXIntel(config={})
        assert otx_intel.update_credentials() is True

    def test_get_value(self):
        test_dict = {
            "foo": {
                "chars": {
                    "a": 1, "b": 2, "c": 3, "d": 4
                },
                "ints": {1: "a", 2: "b"}
            }
        }
        assert getValue(test_dict, ["foo", "chars", "a"]) == test_dict["foo"]["chars"]["a"]

    def test_hostname(self, otx):
        alerts = hostname(otx, self.safe_host)
        assert bool(alerts) is False

    def test_ip(self, otx):
        alerts = ip(otx, self.safe_ip)
        assert bool(alerts) is False

    def test_url(self, otx):
        alerts = url(otx, self.safe_domain)
        assert bool(alerts) is False

    def test_file(self, otx):
        alerts = file(otx, self.safe_file_hash)
        if isinstance(alerts, dict):
            alerts = alerts['alerts']
        assert bool(alerts) is False

    def test_is_ip_malicious(self, otx):
        alerts = is_ip_malicious(ip=self.safe_ip, otx=otx)
        assert bool(alerts) is False

    def test_is_host_malicious(self, otx):
        alerts = is_host_malicious(host=self.safe_host, otx=otx)
        assert bool(alerts) is False

    def test_is_url_malicious(self, otx):
        alerts = is_url_malicious(url=self.safe_domain, otx=otx)
        assert bool(alerts) is False

    def test_is_hash_malicious(self, otx):
        alerts = is_hash_malicious(hash=self.safe_file_hash, otx=otx)
        if isinstance(alerts, dict):
            alerts = alerts['alerts']
        assert bool(alerts) is False

    def test_is_file_malicious(self, otx):
        alerts = is_file_malicious(os.path.realpath(__file__), otx=otx)
        if isinstance(alerts, dict):
            alerts = alerts['alerts']
        assert bool(alerts) is False
