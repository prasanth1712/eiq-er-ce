from .base import BaseApiTest, TestUtils
import unittest, json, random



class GetAllSchema(unittest.TestCase, BaseApiTest):

    def setUp(self):
        super(BaseApiTest, self).__init__()
        super(unittest.TestCase, self).__init__()

    def test_get_all_schema(self):
        response_dict = json.loads(self.get_request(url="/schema"))
        results = self.validate_status_code_and_success_status(response_dict)
        assert bool(results) is True or results is None

    def test_get_a_table_schema(self):
        response_dict = json.loads(self.get_request(url="/schema/account_policy_data"))
        results = self.validate_status_code_and_success_status(response_dict)
        assert bool(results) is True or results is None

    def test_get_a_table_schema_invalid_table_name(self):
        response_dict = json.loads(self.get_request(url="/schema/foobar"))
        results = self.validate_status_code_and_failure_status(response_dict)
        assert results==True


