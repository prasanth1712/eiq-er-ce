from .base import BaseApiTest, TestUtils
import unittest, json, random



class TestIOC(unittest.TestCase, BaseApiTest):

    def setUp(self):
        super(BaseApiTest, self).__init__()
        super(unittest.TestCase, self).__init__()

    def test_get_ioc_list(self):
        response_dict = json.loads(self.get_request(url="/iocs"))
        results = self.validate_status_code_and_success_status(response_dict)
        assert results[1] is not None

    def test_ioc_add_valid_data(self):
        import os
        files = {'file': open(os.getcwd() + '/tests/TestUtilFiles/iocs.json', 'rb')}
        response_dict = json.loads(
            self.post_request(url="/iocs/add", payload=None, is_multipart_form=True, files=files))
        results = self.validate_status_code_and_success_status(response_dict)
        assert bool(results) is True or results is None

    def test_ioc_add_invalid_data(self):
        import os
        files = {'file': open(os.getcwd() + '/tests/TestUtilFiles/iocs_invalid.json', 'rb')}
        response_dict = json.loads(
            self.post_request(url="/iocs/add", payload=None, is_multipart_form=True, files=files))
        results = self.validate_status_code_and_failure_status(response_dict)
        assert bool(results) is True or results is None
