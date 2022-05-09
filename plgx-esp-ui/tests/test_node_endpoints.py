import json


class TestHostsInfo:
    """Test Class to test hosts info
    Data Supplying: A Host
                        host_identifier - foobar
                        platform - windows
    Note:
        is_active should be false
        platform should be windows

    """
    def test_post_hosts_without_filters(self, client, node, url_prefix, token):
        """ Test Case to retrieve all the hosts without any filters
                Observation Needed: A single Host with foobar as host_identifier should be returned
        """
        resp = client.post(url_prefix + '/hosts', headers={'x-access-token': token})
        assert resp.status_code == 200 and json.loads(resp.data)['data']['count']==1

    def test_post_hosts_with_platform_filters(self, client, node, url_prefix, token):
        """ Test Case to retrieve all the hosts with platform filter
                Observation Needed: A single Host with foobar as host_identifier should be returned as its platform is windows
        """
        payload = {'platform':'windows'}
        resp = client.post(url_prefix + '/hosts', headers={'x-access-token': token}, data=payload)
        assert resp.status_code == 200 and json.loads(resp.data)['data']['count']==1

    def test_post_hosts_with_platform_filters_empty_data(self, client, node, url_prefix, token):
        """ Test Case to retrieve all the hosts with platform filter
                Observation Needed: No Host should be returned as there is no host with platform darwin exists!
        """
        payload = {'platform':'darwin'}
        resp = client.post(url_prefix + '/hosts', headers={'x-access-token': token}, data=payload)
        assert resp.status_code == 200 and json.loads(resp.data)['data']['count']==0

    def test_post_hosts_with_status_filters_empty_data(self, client, node, url_prefix, token):
        """ Test Case to retrieve all the hosts with status filter
                Observation Needed: No Host should be returned as there is no online exists!
        """
        payload = {'status':True}
        resp = client.post(url_prefix + '/hosts', headers={'x-access-token': token}, data=payload)
        assert resp.status_code == 200 and json.loads(resp.data)['data']['count']==0

    # def test_post_hosts_with_status_filters(self, client, node, url_prefix, token):
    #     """ Test Case to retrieve all the hosts with status filter
    #             Observation Needed: A Host should be returned as there is a offline host exists!
    #     """
    #     payload = {'status':False}
    #     resp = client.post(url_prefix + '/hosts', headers={'x-access-token': token}, data=payload)
    #     assert resp.status_code == 200 and json.loads(resp.data)['data']['count']==1

    def test_post_hosts_with_pagination(self, client, node, url_prefix, token):
        """ Test Case to retrieve all the hosts with pagination filters
                Observation Needed: A Host should be returned as there is only one exists!
        """
        payload = {'start':0, 'limit':10}
        resp = client.post(url_prefix + '/hosts', headers={'x-access-token': token}, data=payload)
        assert resp.status_code == 200 and json.loads(resp.data)['data']['count']==1


class TestHostDetails:
    """Test Class to test a host details
    Data Supplying: A Host
                        host_identifier - foobar
                        platform - windows
    """
    def test_get_host_details(self, client, node, url_prefix, token):
        """ Test Case to retrieve a host details
        """
        resp = client.get(url_prefix + '/hosts/foobar', headers={'x-access-token': token})
        assert resp.status_code == 200 and json.loads(resp.data)['data']['host_identifier']=='foobar'

    def test_get_host_details_invalid_host_id(self, client, node, url_prefix, token):
        """ Test Case to retrieve a host details for an invalid host_identifier
        """
        resp = client.get(url_prefix + '/hosts/foo', headers={'x-access-token': token})
        assert resp.status_code == 200 and json.loads(resp.data)['data']=={}


class TestHostExport:
    """Test Class to test export host details
    Data Supplying: A Host
                        host_identifier - foobar
                        platform - windows
    """
    def test_get_host_export(self, client, node, url_prefix, token):
        """ Test Case to retrieve csv file of all host details
        """
        resp = client.get(url_prefix + '/hosts/export', headers={'x-access-token': token})
        assert resp.status_code == 200


class TestHostsCount:
    """Test Class to test count of hosts
    Data Supplying: A Host
                        host_identifier - foobar
                        platform - windows
    """
    def test_get_hosts_count(self, client, node, url_prefix, token):
        """ Test Case to retrieve count of all hosts
        """
        resp = client.get(url_prefix + '/hosts/count', headers={'x-access-token': token})
        assert resp.status_code == 200 and ('windows' in json.loads(resp.data)['data'] and 'darwin' in json.loads(resp.data)['data'])


class TestHostStatusLogs:
    """Test Class to test status logs of a host
    Data Supplying: A Host
                        host_identifier - foobar
                        platform - windows
    """
    def test_get_hosts_status_logs(self, client, node, url_prefix, token):
        """ Test Case to retrieve status logs of a host
        """
        resp = client.get(url_prefix + '/hosts/count', headers={'x-access-token': token})
        assert resp.status_code == 200 and ('windows' in json.loads(resp.data)['data'] and 'darwin' in json.loads(resp.data)['data'])