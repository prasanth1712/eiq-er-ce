from polylogyx.domain.config_domain import ConfigDomain


class TestConfigDomain:
    def test_init(self, node):
        cd = ConfigDomain(node=node, remote_addr="127.0.0.1")
        assert cd.node == node
        assert cd.remote_addr == "127.0.0.1"

    def test_get_config(self, db, node):
        cd = ConfigDomain(node=node, remote_addr="127.0.0.1")
        config = cd.get_config()
        assert config == node.get_config()
