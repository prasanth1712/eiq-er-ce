from .base import BaseApiTest, TestUtils
import unittest, json, random



class TestDistributedApis(unittest.TestCase, BaseApiTest):

    def setUp(self):
        super(BaseApiTest, self).__init__()
        super(unittest.TestCase, self).__init__()

    def test_post_distributed_valid_data(self):
        payload = {"query": "select * from system_info"}
        response_dict = json.loads(
            self.post_request(url="/distributed/add", payload=payload))
        results = self.validate_status_code_and_success_status(response_dict)
        assert bool(results) is True or results is None

    def test_post_distributed_with_only_sql_query(self):
        payload = {"query": "select * from system_info"}
        response_dict = json.loads(
            self.post_request(url="/distributed/add", payload=payload))
        results = self.validate_status_code_and_success_status(response_dict)
        assert bool(results) is True or results is None

    def test_post_distributed_with_invalid_sql(self):
        payload = {"query": "select from system_info"}
        response_dict = json.loads(
            self.post_request(url="/distributed/add", payload=payload))
        results = self.validate_status_code_and_failure_status(response_dict)
        assert results == True

