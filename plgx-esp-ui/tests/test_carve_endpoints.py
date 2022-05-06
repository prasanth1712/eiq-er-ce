import json

from .base import TestUtils

test_utils_obj = TestUtils()


class TestNodeCarveList:
    payload = {'host_identifier': '87ed84cc-27b8-11b2-a85c-f63023c322c4', 'start': 0, 'limit': 3}

    def test_node_carve_list_empty_data(self, client, url_prefix, token, node):
        """ Test-case without payloads"""
        resp = client.post(url_prefix + '/carves', headers={'x-access-token': token})
        assert resp.status_code == 200
        response_dict = json.loads(resp.data)
        assert response_dict['status'] == 'success'
        carves = test_utils_obj.get_carve()
        assert response_dict['data'] == carves

        """Test-case with payloads """
        resp = client.post(url_prefix + '/carves', headers={'x-access-token': token}, data=self.payload)
        assert resp.status_code == 200
        response_dict = json.loads(resp.data)
        assert response_dict['status'] == 'failure'
        assert response_dict['message'] == 'Node with this identifier does not exist'
        assert response_dict['data'] is None

    def test_node_carve_list_invalid_url(self, client, url_prefix, token):
        resp = client.post(url_prefix + '/carve', headers={'x-access-token': token}, data=self.payload)
        assert resp.status_code == 404

    def test_node_carve_list_invalid_method(self, client, url_prefix, token):
        resp = client.get(url_prefix + '/carves', headers={'x-access-token': token}, data=self.payload)
        assert resp.status_code == 405

    def test_node_carve_list_data_with_node(self, client, url_prefix, token, carve_session):
        """ Test-case without payloads"""
        resp = client.post(url_prefix + '/carves', headers={'x-access-token': token})
        assert resp.status_code == 200
        response_dict = json.loads(resp.data)
        assert response_dict['status'] == 'success'
        carves = test_utils_obj.get_carve()
        assert response_dict['data'] == carves

        """Test-case with payloads """
        self.payload['host_identifier']='foobar'
        resp = client.post(url_prefix + '/carves', headers={'x-access-token': token}, data=self.payload)
        assert resp.status_code == 200
        response_dict = json.loads(resp.data)
        assert response_dict['status'] == 'success'
        carves = test_utils_obj.get_carves_with_host_identifier(self.payload['host_identifier'])
        assert response_dict['data'] == carves


class TestDownloadCarves:
    def test_download_carves_empty_data(self, client, url_prefix, token):
        resp = client.get(url_prefix + '/carves/download/MQIAPXX285', headers={'x-access-token': token})
        assert resp.status_code == 200
        response_dict = json.loads(resp.data)
        assert response_dict['status'] == 'failure'
        assert response_dict['message'] == 'This session id does not exist'

    def test_download_carves_invalid_url(self, client, url_prefix, token):
        resp = client.get(url_prefix + '/carves/download', headers={'x-access-token': token})
        assert resp.status_code == 404

    def test_download_carves_invalid_method(self, client, url_prefix, token):
        resp = client.post(url_prefix + '/carves/download/MQIAPXX285', headers={'x-access-token': token})
        assert resp.status_code == 405

    def test_download_carves_with_data(self, client, url_prefix, token, carve_session):
        resp = client.get(url_prefix + '/carves/download/MQIAPXX285', headers={'x-access-token': token})
        assert resp.status_code == 200
        response_dict = json.loads(resp.data)
        get_file = test_utils_obj.get_carves_file('MQIAPXX285')
        assert response_dict['data'] == get_file


class TestCarveSessionByPostQueryId:

    payload = {"query_id": "", "host_identifier": ""}

    def test_carve_session_by_post_without_data(self, client, url_prefix, token):

        """ Test-case with empty host_identifier and query_id """
        resp = client.post(url_prefix + '/carves/query', headers={'x-access-token': token}, data=self.payload)
        assert resp.status_code == 200
        response_dict = json.loads(resp.data)
        assert response_dict['status'] == 'failure'
        assert response_dict['message'] == 'Node with this identifier does not exist'

        """ Test-case without payload """
        resp = client.post(url_prefix + '/carves/query', headers={'x-access-token': token})
        assert resp.status_code == 400

        """ test-case with empty payload """
        resp = client.post(url_prefix + '/carves/query', headers={'x-access-token': token}, data={})
        assert resp.status_code == 400

    def test_carve_session_by_post_query_id_invalid_url(self, client, url_prefix, token):
        resp = client.post(url_prefix + '/carve/query', headers={'x-access-token': token}, data=self.payload)
        assert resp.status_code == 404

    def test_carve_session_by_post_query_id_invalid_method(self, client, url_prefix, token):
        resp = client.get(url_prefix + '/carves/query', headers={'x-access-token': token}, data=self.payload)
        assert resp.status_code == 405

    def test_carve_session_by_post_with_data(self, client, url_prefix, token, carve_session, distributed_query_task):

        """ Test-case with host_identifier and query_id """
        self.payload["host_identifier"] = "foobar"
        self.payload["query_id"] = 1
        resp = client.post(url_prefix + '/carves/query', headers={'x-access-token': token}, data=self.payload)
        assert resp.status_code == 200
        response_dict = json.loads(resp.data)
        assert response_dict['status'] == 'success'
        carve_session = test_utils_obj.get_carve_session_by_query_id(self.payload['query_id'],
                                                                     self.payload['host_identifier'])
        assert response_dict['data'] == carve_session

        """ Test-case with host_identifier but wrong query_id """
        self.payload["host_identifier"] = "foobar"
        self.payload["query_id"] = 2
        resp = client.post(url_prefix + '/carves/query', headers={'x-access-token': token}, data=self.payload)
        assert resp.status_code == 200
        response_dict = json.loads(resp.data)
        assert response_dict['status'] == 'failure'
        assert response_dict['message'] == 'Query id provided is invalid'


class TestDeleteCarveSessionByPostSessionId:

    payload = {'session_id': ''}

    def test_delete_carve_session_without_data(self, client, url_prefix, token):
        """ Test-case without payloads """
        resp = client.post(url_prefix + '/carves/delete', headers={'x-access-token': token})
        assert resp.status_code == 400

        """ Test-case with empty paylods """
        resp = client.post(url_prefix + '/carves/delete', headers={'x-access-token': token}, data={})
        assert resp.status_code == 400

        """ Test-case with empty session-id """
        resp = client.post(url_prefix + '/carves/delete', headers={'x-access-token': token}, data=self.payload)
        assert resp.status_code == 200
        response_dict = json.loads(resp.data)
        assert response_dict['status'] == 'failure'
        assert response_dict['message'] == 'Carve for the session id is not found!'
        assert response_dict['data'] is None

    def test_delete_carve_session_invalid_url(self, client, url_prefix, token):
        resp = client.post(url_prefix + '/carve/delete', headers={'x-access-token': token}, data=self.payload)
        assert resp.status_code == 404

    def test_delete_carve_session_invalid_method(self, client, url_prefix, token):
        resp = client.get(url_prefix + '/carves/delete', headers={'x-access-token': token}, data=self.payload)
        assert resp.status_code == 405

    def test_carve_session_with_data(self, client, url_prefix, token, carve_session):
        """ Test-case with valid session-id """
        self.payload['session_id'] = 'MQIAPXX285'
        resp = client.post(url_prefix + '/carves/delete', headers={'x-access-token': token}, data=self.payload)
        assert resp.status_code == 200
        response_dict = json.loads(resp.data)
        assert response_dict['status'] == 'success'
        assert response_dict['message'] == 'Successfully deleted the carve for the session id given!'

        """ Test-case with invalid session-id """
        self.payload['session_id'] = 'MQIAPXX85'
        resp = client.post(url_prefix + '/carves/delete', headers={'x-access-token': token}, data=self.payload)
        assert resp.status_code == 200
        response_dict = json.loads(resp.data)
        assert response_dict['status'] == 'failure'
        assert response_dict['message'] == 'Carve for the session id is not found!'
