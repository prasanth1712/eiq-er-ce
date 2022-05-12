from .base import BaseApiTest, TestUtils
import unittest, json, random



class GetRule(unittest.TestCase, BaseApiTest):

    def setUp(self):
        super(BaseApiTest, self).__init__()
        super(unittest.TestCase, self).__init__()

    def test_get_all_rules(self):
        response_dict = json.loads(self.get_request(url="/rules/"))
        results = self.validate_status_code_and_success_status(response_dict)
        assert bool(results) is True or results is None

    def test_get_rule_by_id_valid(self):
        response_dict = json.loads(self.get_request(url="/rules/1"))
        results = self.validate_status_code_and_success_status(response_dict)
        assert bool(results) is True or results is None

class AddOrModifyRule(unittest.TestCase, BaseApiTest):

    def setUp(self):
        super(BaseApiTest, self).__init__()
        super(unittest.TestCase, self).__init__()

    def test_add_rule(self):
        pass

    def test_edit_rule_valid_rule_id(self):
        pass

    def test_edit_rule_invalid_rule_id(self):
        pass

    def test_add_rule_invalid_data(self):
        pass