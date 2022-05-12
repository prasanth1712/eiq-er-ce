from .base import BaseApiTest, TestUtils
import unittest, json, random



class GetQuery(unittest.TestCase, BaseApiTest):

    def setUp(self):
        super(BaseApiTest, self).__init__()
        super(unittest.TestCase, self).__init__()

    def test_get_all_queries(self):
        response_dict = json.loads(self.get_request(url="/queries/"))
        results = self.validate_status_code_and_success_status(response_dict)
        assert bool(results) is True or results is None

    def test_get_query_by_id_valid(self):
        response_dict = json.loads(self.get_request(url="/queries/1"))
        results = self.validate_status_code_and_success_status(response_dict)
        assert bool(results) is True or results is None

    def test_get_query_by_id_invalid(self):
        response_dict = json.loads(self.get_request(url="/queries/1234567891"))
        results = self.validate_status_code_and_failure_status(response_dict)
        assert results==True

class AddQuery(unittest.TestCase, BaseApiTest):

    def setUp(self):
        super(BaseApiTest, self).__init__()
        super(unittest.TestCase, self).__init__()

    def test_add_query(self):
        payload = {"name": "foobar",
                   "query": "select * from time;",
                   "interval": 10}
        response_dict = json.loads(
            self.post_request(url="/queries/add", payload=payload))
        results = self.validate_status_code_and_success_status(response_dict)
        assert bool(results) is True or results is None

    def test_edit_tags_of_query(self):
        payload = {"query_id": 1,
                   "add_tags":["foo"],
                   "remove_tags": ["foobar"]}
        response_dict = json.loads(
            self.post_request(url="/queries/tag/edit", payload=payload))
        results = self.validate_status_code_and_success_status(response_dict)
        assert bool(results) is True or results is None