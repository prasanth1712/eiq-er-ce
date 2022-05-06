from .base import BaseApiTest, TestUtils
import unittest, json, random



class GetPack(unittest.TestCase, BaseApiTest):

    def setUp(self):
        super(BaseApiTest, self).__init__()
        super(unittest.TestCase, self).__init__()

    def test_get_all_packs(self):
        response_dict = json.loads(self.get_request(url="/packs/"))
        results = self.validate_status_code_and_success_status(response_dict)
        assert bool(results) is True or results is None

    def test_get_pack_by_id_valid_id(self):
        response_dict = json.loads(self.get_request(url="/packs/1"))
        results = self.validate_status_code_and_success_status(response_dict)
        assert bool(results) is True or results is None

    def test_get_pack_by_id_invalid_id(self):
        response_dict = json.loads(self.get_request(url="/packs/12345678910"))
        results = self.validate_status_code_and_failure_status(response_dict)
        assert bool(results) is True or results is None

class AddPack(unittest.TestCase, BaseApiTest):

    def setUp(self):
        super(BaseApiTest, self).__init__()
        super(unittest.TestCase, self).__init__()
        self.utils_obj = TestUtils()

    def test_add_pack_valid_input(self):
        query_dict = self.utils_obj.get_query_dict()
        payload = {"name":"foobar","queries": {query_dict['name']:{'query':query_dict['sql'], 'interval':30}}, "tags":["foo","foobar"]}
        response_dict = json.loads(
            self.post_request(url="/packs/add", payload=payload))
        results = self.validate_status_code_and_success_status(response_dict)
        assert bool(results) is True or results is None

    def test_add_pack_invalid_input(self):
        payload = {"name": "foobar", "queries": "foobar","tags": ["foo", "foobar"]}
        response_dict = json.loads(
            self.post_request(url="/packs/add", payload=payload))
        assert int(response_dict['response_code']) == 400


    def test_add_pack_through_json_file(self):
        pass

class EditTagsOfPack(unittest.TestCase, BaseApiTest):

    def setUp(self):
        super(BaseApiTest, self).__init__()
        super(unittest.TestCase, self).__init__()
        self.utils_obj = TestUtils()

    def test_edit_tags_of_pack_with_tags(self):
        id=self.utils_obj.get_pack()['id']
        payload = {"pack_id":id, "add_tags":["foobar", "foo"], "remove_tags":["foo1", "test"]}
        response_dict = json.loads(
            self.post_request(url="/packs/tag/edit", payload=payload))
        results = self.validate_status_code_and_success_status(response_dict)
        assert bool(results) is True or results is None

    def test_list_tags_of_pack(self):
        name = self.utils_obj.get_pack()['name']
        response_dict = json.loads(
            self.get_request(url="/packs/"+name+"/tags"))
        results = self.validate_status_code_and_success_status(response_dict)
        assert bool(results) is True or results is None
