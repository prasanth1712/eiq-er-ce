from .base import BaseApiTest, TestUtils
import unittest, json, random



# class GetConfigsInfo(unittest.TestCase, BaseApiTest):
#
#     def setUp(self):
#         super(BaseApiTest, self).__init__()
#         super(unittest.TestCase, self).__init__()
#
#     def test_get_all_configs_found(self):
#         response_dict = json.loads(self.get_request(url="/configs/"))
#         results = self.validate_status_code_and_success_status(response_dict)
#         self.config_id = results[1][random.randint(0,len(results[1]))]['id']
#         assert bool(results) is True or results is None
#
#     def test_get_config_id_given_found(self):
#         response_dict = json.loads(self.get_request(url="/configs/"+self.config_id))
#         results = self.validate_status_code_and_success_status(response_dict)
#         assert bool(results) is True or results is None
#
#     def test_post_list_of_tags(self):
#         payload = {"tags":["foo2", "foo1"]}
#         response_dict = json.loads(
#             self.post_request(url="/tags/add", payload=payload))
#         results = self.validate_status_code_and_success_status(response_dict)
#         assert bool(results) is True or results is None
#
# class AddConfig(unittest.TestCase, BaseApiTest):
#
#     def setUp(self):
#         super(BaseApiTest, self).__init__()
#         super(unittest.TestCase, self).__init__()
