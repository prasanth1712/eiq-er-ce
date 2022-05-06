from .base import BaseApiTest, TestUtils
import unittest, json, random



class TestYara(unittest.TestCase, BaseApiTest):

    def setUp(self):
        super(BaseApiTest, self).__init__()
        super(unittest.TestCase, self).__init__()

    def test_1add_yara(self):
        import os
        files = {'file':open(os.getcwd()+'/tests/TestUtilFiles/eicar.yara', 'rb')}
        response_dict = json.loads(
            self.post_request(url="/yara/add", payload=None, is_multipart_form=True, files=files))
        assert response_dict['response_code'] == 200

    def test_2get_yara_list(self):
        response_dict = json.loads(self.get_request(url="/yara"))
        results = self.validate_status_code_and_success_status(response_dict)
        assert bool(results) is True or results is None

    def test_3file_view_yara(self):
        payload = {'file_name':'eicar.yara'}
        response_dict = json.loads(
            self.post_request(url="/yara/view", payload=payload))
        results = self.validate_status_code_and_success_status(response_dict)
        assert bool(results) is True or results is None

    def test_4view_yara_filename_invalid(self):
        payload = {'file_name':'abcdsjefhfdk.yara'}
        response_dict = json.loads(
            self.post_request(url="/yara/view", payload=payload))
        results = self.validate_status_code_and_failure_status(response_dict)
        assert bool(results) is True or results is None

    def test_5delete_yara(self):
        payload = {'file_name':'eicar.yara'}
        response_dict = json.loads(
            self.post_request(url="/yara/delete", payload=payload))
        results = self.validate_status_code_and_success_status(response_dict)
        assert bool(results) is True or results is None

    def test_6delete_yara_filename_invalid(self):
        payload = {'file_name':'abcdsjefhfdk.yara'}
        response_dict = json.loads(
            self.post_request(url="/yara/delete", payload=payload))
        results = self.validate_status_code_and_failure_status(response_dict)
        assert bool(results) is True or results is None
