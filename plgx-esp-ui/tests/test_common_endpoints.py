from polylogyx.blueprints.v1.utils import *
from .base import TestUtils

test_utils_obj = TestUtils()


class TestHuntFileUpload:
    fp = 'tests/eicar.com.txt'
    files = {'file': open(fp, 'rb')}
    payload = {'file': files, 'type': 'md5'}

    def test_with_empty_data(self, client, url_prefix, token):

        """ Test-case without payload """
        resp = client.post(url_prefix + '/common_api/hunt-upload', headers={'x-access-token': token})
        assert resp.status_code == 400

        """ Test-case with payloads of upload file and type """
        resp = client.post(url_prefix + '/common_api/hunt-upload', headers={'x-access-token': token},
                           data=self.payload)
        assert resp.status_code == 200
        response_dict = json.loads(resp.data)
        assert response_dict['status'] == 'success'
        assert response_dict['message'] == 'Successfully fetched the results through the hunt file uploaded'
        assert response_dict['data'] == {}

        """ Test-case with upload file, type and host-identifier but no query-name """
        self.payload['host_identifier'] = 'foobar'
        self.payload['file'] = {'file': open(self.fp, 'rb')}
        resp = client.post(url_prefix + '/common_api/hunt-upload', headers={'x-access-token': token},
                           data=self.payload)
        assert resp.status_code == 200
        response_dict = json.loads(resp.data)
        assert response_dict['status'] == 'failure'
        assert response_dict['data'] is None

        """ Test-case with paylods of upload file, type, host-identifier and query-name """
        self.payload['query_name'] = 'kernel_modules'
        self.payload['file'] = {'file': open(self.fp, 'rb')}
        resp = client.post(url_prefix + '/common_api/hunt-upload', headers={'x-access-token': token},
                           data=self.payload)
        assert resp.status_code == 200
        response_dict = json.loads(resp.data)
        assert response_dict['status'] == 'success'
        assert response_dict['message'] == 'Successfully fetched the results through the hunt file uploaded'
        assert response_dict['data'] == []

    def test_with_invalid_url(self, client, url_prefix, token):
        self.payload['file'] = {'file': open(self.fp, 'rb')}
        resp = client.post(url_prefix + '/common-api/hunt-upload', headers={'x-access-token': token},
                           data=self.payload)
        assert resp.status_code == 404

    def test_with_invalid_method(self, client, url_prefix, token):
        self.payload['file'] = {'file': open(self.fp, 'rb')}
        resp = client.get(url_prefix + '/common_api/hunt-upload', headers={'x-access-token': token},
                          data=self.payload)
        assert resp.status_code == 405

    def test_data_without_host_identifier(self, client, url_prefix, token, node, result_log):
        """ Test-case with file-upload and type but no host-identifier """

        self.payload['file'] = {'file': open(self.fp, 'rb')}
        self.payload['host_identifier'] = ''
        self.payload['query_name'] = ''
        resp = client.post(url_prefix + '/common_api/hunt-upload', headers={'x-access-token': token},
                           data=self.payload)
        assert resp.status_code == 200
        response_dict = json.loads(resp.data)
        assert response_dict['status'] == "success"
        assert response_dict['message'] == "Successfully fetched the results through the hunt file uploaded"
        file = open(self.fp, 'rb')
        lines = [line.decode('utf-8').replace('\n', '') for line in file.readlines()]
        data = test_utils_obj.get_hunt_data(file, lines, 'md5')
        assert response_dict['data'] == data

    def test_data_with_host_identifier(self, client, url_prefix, token, node, result_log):
        """ Test-case with host-identifier, file upload and type but no query-name """

        self.payload['host_identifier'] = 'foobar'
        self.payload['file'] = {'file': open(self.fp, 'rb')}
        self.payload['query_name'] = ''

        resp = client.post(url_prefix + '/common_api/hunt-upload', headers={'x-access-token': token},
                           data=self.payload)
        assert resp.status_code == 200
        response_dict = json.loads(resp.data)
        assert response_dict['status'] == 'failure'
        assert response_dict['message'] == 'Please provide the query name'
        file = open(self.fp, 'rb')
        lines = [line.decode('utf-8').replace('\n', '') for line in file.readlines()]
        data = test_utils_obj.get_hunt_data(file, lines, 'md5', 'foobar')
        assert response_dict['data'] == data

        """ Test-case with only host-identifier, file upload, type and query-name """

        self.payload['host_identifier'] = 'foobar'
        self.payload['file'] = {'file': open(self.fp, 'rb')}
        self.payload['query_name'] = 'kernel_modules'

        resp = client.post(url_prefix + '/common_api/hunt-upload', headers={'x-access-token': token},
                           data=self.payload)
        assert resp.status_code == 200
        response_dict = json.loads(resp.data)
        assert response_dict['status'] == "success"
        assert response_dict['message'] == "Successfully fetched the results through the hunt file uploaded"
        file = open(self.fp, 'rb')
        lines = [line.decode('utf-8').replace('\n', '') for line in file.readlines()]
        data = test_utils_obj.get_hunt_data(file, lines, 'md5', 'foobar', 'kernel_modules')
        assert response_dict['data'] == data


class TestIndicatorHunt:

    payload = {
        'indicators': 'X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*',
        'type': 'md5'
    }

    def test_indicator_hunt_with_empty_data(self, client, url_prefix, token):
        """ Test-case without payloads """
        resp = client.post(url_prefix + '/common_api/indicators/hunt', headers={'x-access-token': token})
        assert resp.status_code == 400

        """ Test-case with empty payload """
        resp = client.post(url_prefix + '/common_api/indicators/hunt', headers={'x-access-token': token},
                           data={})
        assert resp.status_code == 400

        """ Test-case with payload of indicators and type but no host_identifier and no query-name """
        resp = client.post(url_prefix + '/common_api/indicators/hunt', headers={'x-access-token': token},
                           data=self.payload)
        assert resp.status_code == 200
        response_dict = json.loads(resp.data)
        assert response_dict['status'] == 'success'
        assert response_dict['message'] == 'Successfully fetched the results through the indicators provided'
        assert response_dict['data'] == {}

        """ Test-case with payload of indicators, type and host-identifier but no query-name """
        self.payload['host_identifier'] = 'foobar'
        resp = client.post(url_prefix + '/common_api/indicators/hunt', headers={'x-access-token': token},
                           data=self.payload)
        assert resp.status_code == 200
        response_dict = json.loads(resp.data)
        assert response_dict['status'] == 'failure'
        assert response_dict['message'] == 'Please provide the query name'
        assert response_dict['data'] is None

        """ Test-case with payload of indicators, type, host_identifier and query-name """
        self.payload['query_name'] = 'kernel_modules'
        resp = client.post(url_prefix + '/common_api/indicators/hunt', headers={'x-access-token': token},
                           data=self.payload)
        assert resp.status_code == 200
        response_dict = json.loads(resp.data)
        assert response_dict['status'] == 'success'
        assert response_dict['message'] == 'Successfully fetched the results through the indicators provided'
        assert response_dict['data'] == []

    def test_indicator_hunt_with_invalid_url(self, client, url_prefix, token):
        resp = client.post(url_prefix + '/common-api/indicators/hunt', headers={'x-access-token': token},
                           data=self.payload)
        assert resp.status_code == 404

    def test_indicator_hunt_with_invalid_method(self, client, url_prefix, token):
        resp = client.get(url_prefix + '/common_api/indicators/hunt', headers={'x-access-token': token},
                           data=self.payload)
        assert resp.status_code == 405

    def test_indicator_hunt_with_data(self, client, url_prefix, token, node, result_log):
        """ Test-case only indicators and type but no host-identifier and no query-name"""
        self.payload['host_identifier'] = ''
        self.payload['query_name'] = ''
        resp = client.post(url_prefix + '/common_api/indicators/hunt', headers={'x-access-token': token},
                           data=self.payload)
        assert resp.status_code == 200
        response_dict = json.loads(resp.data)
        assert response_dict['status'] == 'success'
        data = test_utils_obj.get_hunt_data(self.payload['indicators'].split(','), self.payload['type'])
        assert response_dict['data'] == data

        """ Test-case with indicators, type and host-identifier but no query-name """
        self.payload['host_identifier'] = 'foobar'
        resp = client.post(url_prefix + '/common_api/indicators/hunt', headers={'x-access-token': token},
                           data=self.payload)
        assert resp.status_code == 200
        response_dict = json.loads(resp.data)
        assert response_dict['status'] == 'failure'
        assert response_dict['message'] == 'Please provide the query name'
        assert response_dict['data'] is None

        """ Test-case with indicators, type, host-identifier and query-name """
        self.payload['host_identifier'] = 'foobar'
        self.payload['query_name'] = 'kernel_modules'
        resp = client.post(url_prefix + '/common_api/indicators/hunt', headers={'x-access-token': token},
                           data=self.payload)
        assert resp.status_code == 200
        response_dict = json.loads(resp.data)
        assert response_dict['status'] == 'success'
        data = test_utils_obj.get_hunt_data(self.payload['indicators'].split(','), self.payload['type'],
                                            self.payload['host_identifier'], self.payload['query_name'])
        assert response_dict['data'] == data


class TestSearch:

    payload={}

    def test_search_with_empty_data(self, client, url_prefix, token):
        resp = client.post(url_prefix + '/common_api/search', headers={'x-access-token': token})
        assert resp.status_code == 400


class TestDeleteQueryResult:

    payload = {'days_of_data': None}

    def test_delete_query_result_with_empty_data(self, client, url_prefix, token):

        """ Test-case without payload """
        resp = client.post(url_prefix + '/common_api/queryresult/delete', headers={'x-access-token': token})
        assert resp.status_code == 400

        """ Test-case with invalid payload """
        resp = client.post(url_prefix + '/common_api/queryresult/delete', headers={'x-access-token': token})
        assert resp.status_code == 400

        """ Test-case with valid Payload """
        self.payload['days_of_data'] = 2
        resp = client.post(url_prefix + '/common_api/queryresult/delete', headers={'x-access-token': token},
                           data=self.payload)
        assert resp.status_code == 200
        response_dict = json.loads(resp.data)
        assert response_dict['status'] == 'success'
        assert response_dict['message'] == 'Query result data is deleted successfully'

    def test_delete_query_result_with_invalid_url(self, client, url_prefix, token):
        resp = client.post(url_prefix + '/common_api/queryresult/delete', headers={'x-access-token': token},
                           data=self.payload)
        assert resp.status_code == 200

    def test_query_result_with_invalid_method(self, client, url_prefix, token):
        resp = client.get(url_prefix + '/common_api/queryresult/delete', headers={'x-access-token':token},
                          data=self.payload)
        assert resp.status_code == 405

    def test_delete_query_result_with_data(self, client, url_prefix, token, node, result_log):
        self.payload['days_of_data'] = 2
        resp = client.post(url_prefix + '/common_api/queryresult/delete', headers={'x-access-token': token},
                           data=self.payload)
        assert resp.status_code == 200
        response_dict = json.loads(resp.data)
        assert response_dict['status'] == 'success'
        assert response_dict['message'] == 'Query result data is deleted successfully'


class TestExportScheduleQueryCSV:

    payload = {'query_name': '', 'host_identifier': ''}

    def test_export_schedule_query_with_empty_data(self, client, url_prefix, token):
        """ Test-case without payloads """
        resp = client.post(url_prefix + '/common_api/schedule_query/export', headers={'x-access-token':token})
        assert resp.status_code == 400

        """ Test-case with empty Payloads """
        resp = client.post(url_prefix + '/common_api/schedule_query/export', headers={'x-access-token': token},
                           data=self.payload)
        assert resp.status_code == 200
        response_dict = json.loads(resp.data)
        assert response_dict['status'] == 'failure'
        assert response_dict['message'] == 'Node doesnot exists fot the id given'

