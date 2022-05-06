from .base import BaseApiTest, TestUtils
import unittest, json, random



class GetTagsInfo(unittest.TestCase, BaseApiTest):

    def setUp(self):
        super(BaseApiTest, self).__init__()
        super(unittest.TestCase, self).__init__()

    def test_get_all_tags_found(self):
        response_dict = json.loads(self.get_request(url="/tags"))
        results = self.validate_status_code_and_success_status(response_dict)
        assert bool(results) is True or results is None

    def test_add_list_of_tags(self):
        payload = {"tags":"foo2,foo1"}
        response_dict = json.loads(self.post_request(url="/tags/add", payload=payload))
        results = self.validate_status_code_and_success_status(response_dict)
        assert bool(results) is True or results is None

    def test_post_list_of_tags_length_invalid(self):
        payload = {"tags":"foocnajdfdssfjrnefmegtenkfmdbwo2,foo1njdnlsreiejfnjnriefenrifnriemo"}
        response_dict = json.loads(self.post_request(url="/tags/add", payload=payload))
        results = self.validate_status_code_and_failure_status(response_dict)
        assert bool(results) is True or results is None

    def test_post_delete_tags(self):
        payload = {"tags":"foo2,foo1"}
        response_dict = json.loads(self.post_request(url="/tags/delete", payload=payload))
        results = self.validate_status_code_and_success_status(response_dict)
        assert bool(results) is True or results is None
