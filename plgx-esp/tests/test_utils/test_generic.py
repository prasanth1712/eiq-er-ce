from polylogyx.utils import generic as g


class TestGeneric:

    def test_merge_two_dicts(self):
        a = {"a":"A"}
        b ={"b":"B"}
        res = g.merge_two_dicts(a,b) 
        assert "a" in res
        assert "b" in res
    
    def test_merge_two_dicts_no_inps(self):
        res = g.merge_two_dicts(None,None) 
        assert res == {}
    

    def test_flatten_json(self):
        inp = {"columns":{"key":"value"}}
        res = g.flatten_json(inp)
        assert "key" in res
        assert res["key"]=="value"


    def test_is_wildcard_match(self):
        pass      

