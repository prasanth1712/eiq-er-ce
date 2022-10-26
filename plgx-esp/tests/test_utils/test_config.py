from polylogyx.utils.config import get_node_configuration, assemble_options, assemble_packs, \
    assemble_distributed_queries, assemble_configuration
from celery.result import AsyncResult


class TestConfigUtils:

    def test_get_node_configuration(self, node):
        config_dict = get_node_configuration(node)
        assert config_dict['foo'] == 'foobar'
        assert 'foo' in config_dict['schedule']
        assert config_dict['schedule']['foo']['query'] == 'foobar'

    def test_assemble_configuration(self, node):
        config = assemble_configuration(node)
        assert config['foo'] == 'foobar'
        assert 'foo' in config['schedule']
        assert config['schedule']['foo']['query'] == 'foobar'

    def test_assemble_packs(self, db, query, pack, tag, node):
        pack.queries.append(query)
        pack.tags.append(tag)
        node.tags.append(tag)
        db.session.commit()
        query_packs = assemble_packs(node)
        assert 'test_pack' in query_packs and query_packs['test_pack']['name'] == 'test_pack'
        assert 'test_query' in query_packs['test_pack']['queries'] and \
               query_packs['test_pack']['queries']['test_query']['query'] == 'foobar'

    def test_assemble_distributed_queries(self, node, distributed_query):
        queries = assemble_distributed_queries(node=node)
        found = False
        for key, value in queries.items():
            if value == 'foobar':
                found = True
        assert found is True
