from polylogyx.db.models import Node

class TestDatabase:
    def test_delete_mixin(self,db):
        node=Node(host_identifier="foobar")
        node.save()
        cnt = Node.query.count()
        assert cnt == 1
        node.delete()
        cnt = Node.query.count()
        assert cnt == 0

    def test_get_by_id(self,db):
        node = Node.get_by_id(None)
        assert node is None 
        