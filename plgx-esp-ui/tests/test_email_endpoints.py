from .base import BaseApiTest, TestUtils
import unittest, json, random


class TestEmailConfigure(unittest.TestCase, BaseApiTest):
    def setUp(self):
        super(BaseApiTest, self).__init__()
        super(unittest.TestCase, self).__init__()

    def test_get_email_configuration(self):
        response_dict = json.loads(self.get_request(url="/email/configure"))
        results = self.validate_status_code_and_success_status(response_dict)
        assert bool(results) is True or results is None

    def test_email_configure_with_valid_data(self):
        payload = {"email": "test@gmail.com", "smtpPort": 12, "smtpAddress":"smtp2.g mail.com" , "password": "foobar", "emailRecipients":"polylogyx@gmail.com,test2@gmail.com"}
        response_dict = json.loads(self.post_request(url="/email/configure", payload=payload))
        results = self.validate_status_code_and_success_status(response_dict)
        assert bool(results) is True or results is None

    def test_email_configure_with_missed_data(self):
        payload = {"email": "test@gmail.com", "password": "foobar", "emailRecipients":"polylogyx@gmail.com,test2@gmail.com"}
        response_dict = json.loads(self.post_request(url="/email/configure", payload=payload))
        assert int(response_dict['response_code']) == 400

    def test_send_test_email(self):
        payload = {}
        response_dict = json.loads(self.post_request(url="/email/test", payload=payload))
        results = self.validate_status_code_and_success_status(response_dict)
        assert bool(results) is True or results is None

