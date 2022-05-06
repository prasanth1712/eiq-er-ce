from polylogyx.domain.dist_queries_domain import DistQueriesDomain

from ..factories import DistributedQueryTaskFactory


class TestDistQueriesDomain:
    def test_init(self, node):
        dqd = DistQueriesDomain(node, remote_addr="127.0.0.1")
        assert dqd.node == node

    # def test_read(self,db,node):
    #     dqd = DistQueriesDomain(node,remote_addr="127.0.0.1")
    #     DistributedQueryTaskFactory(node=node,priority=0)
    #     queries = dqd.read()
    #     assert len(queries)>0
