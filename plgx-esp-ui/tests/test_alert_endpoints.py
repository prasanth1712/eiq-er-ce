from polylogyx.dao.v1 import alerts_dao as dao
from polylogyx.wrappers.v1 import alert_wrappers as alert_wrapper
from polylogyx.blueprints.v1.utils import *

ALERT_RECON_QUERIES_JSON = {
    "scheduled_queries": [
        {
            "name": "win_file_events",
            "before_event_interval": 30,
            "after_event_interval": 60
        },
        {
            "name": "win_process_events",
            "before_event_interval": 30,
            "after_event_interval": 60
        }, {
            "name": "win_registry_events",
            "before_event_interval": 30,
            "after_event_interval": 60
        }, {
            "name": "win_socket_events",
            "before_event_interval": 30,
            "after_event_interval": 60
        }, {
            "name": "win_http_events",
            "before_event_interval": 30,
            "after_event_interval": 60
        }
    ],
    "live_queries": [
        {
            "name": "win_epp_table",
            "query": "select * from win_epp_table;"
        }
    ]
}


class TestPostViewAlerts:

    payload = {'host_identifier': '', 'rule_id': None, 'query_name': ''}

    def test_valid_post_alerts_empty_data(self, client, url_prefix, token):
        """ Test-Case with no payload """
        resp = client.post(url_prefix + '/alerts', headers={'x-access-token': token}, data=self.payload)
        assert resp.status_code == 200
        response_dict = json.loads(resp.data)
        assert response_dict['status'] == 'failure'
        assert response_dict['message'] == 'no data is given to view alerts'
        assert response_dict['data'] == []

        """ Test-Case with only rule_id """
        self.payload['rule_id'] = 1
        resp = client.post(url_prefix + '/alerts', headers={'x-access-token': token}, data=self.payload)
        assert resp.status_code == 200
        response_dict = json.loads(resp.data)
        assert response_dict['status'] == 'failure'
        assert response_dict['message'] == 'rule_id is invalid or might be there is no matching data'
        assert response_dict['data'] == []

        """ Test-Case only with Host-Identifier """
        self.payload['rule_id'] = None
        self.payload['host_identifier'] = 'foobar'
        resp = client.post(url_prefix + '/alerts', headers={'x-access-token': token}, data=self.payload)
        assert resp.status_code == 200
        response_dict = json.loads(resp.data)
        assert response_dict['message'] == "Host_identifier given is not valid!"
        assert response_dict['data'] == []

        """ Test-Case only with Query-Name """
        self.payload['query_name'] = 'win_file_events'
        self.payload['host_identifier'] = ''
        resp = client.post(url_prefix + '/alerts', headers={'x-access-token': token}, data=self.payload)
        assert resp.status_code == 200
        response_dict = json.loads(resp.data)
        assert response_dict['message'] == 'query_name is invalid or might be there is no matching data'
        assert response_dict['data'] == []

    def test_post_view_alerts_invalid_url(self, client, url_prefix, token):
        resp = client.post(url_prefix + '/alert', headers={'x-access-token': token}, data=self.payload)
        assert resp.status_code == 404

    def test_valid_post_alerts_with_data(self, client, url_prefix, token, alerts):
        self.payload['host_identifier'] = 'foobar'
        self.payload['rule_id'] = 1
        self.payload['query_name'] = 'win_file_events'
        resp = client.post(url_prefix + '/alerts', headers={'x-access-token': token}, data=self.payload)
        assert resp.status_code == 200
        response_dict = json.loads(resp.data)
        assert response_dict['status'] == 'success'
        assert response_dict['message'] == 'Successfully received the alerts'
        node = node_dao.get_node_by_host_identifier(self.payload['host_identifier'])
        assert response_dict['data'] == add_rule_name_to_alerts_response(marshal(dao.get_alerts_for_input(node, self.payload['rule_id'], self.payload['query_name'])[0], alert_wrapper.alerts_wrapper, skip_none=True))

    def test_invalid_method_for_view_alerts(self, client, url_prefix, token):
        resp = client.get(url_prefix + '/alerts', headers={'x-access-token': token}, data=self.payload)
        assert resp.status_code == 405


class TestGetAlertsGraphData:

    def test_valid_alerts_with_empty_data(self, client, url_prefix, token):
        resp = client.get(url_prefix + '/alerts/graph', headers={'x-access-token': token})
        assert resp.status_code == 200
        response_dict = json.loads(resp.data)
        assert response_dict['status'] == 'failure'
        assert response_dict['data'] is None

    def test_valid_alerts_with_data(self, client, url_prefix, token, alerts, result_log):
        resp = client.get(url_prefix + '/alerts/graph', headers={'x-access-token': token})
        assert resp.status_code == 200
        response_dict = json.loads(resp.data)
        assert response_dict['status'] == 'success'
        assert response_dict['data'] == get_alerts_data()

    def test_get_alerts_invalid_url(self, client, url_prefix, token):
        resp = client.get(url_prefix + '/alerts/graphs', headers={'x-access-token': token})
        assert resp.status_code == 404

    def test_invalid_request(self, client, url_prefix, token):
        resp = client.post(url_prefix + '/alerts/graph', headers={'x-access-token': token})
        assert resp.status_code == 405


class TestPostAlertsData:

    start, limit, source = 4, 5, "rule"
    payload = {"start": start, "limit": limit, "source": source}

    def test_valid_alerts_without_data(self, url_prefix, client, token):
        resp = client.post(url_prefix + '/alerts/data', headers={'x-access-token': token}, data=self.payload)
        assert resp.status_code == 200

        response_dict = json.loads(resp.data)
        assert response_dict['status'] == 'failure'
        assert response_dict['data'] == []

    def test_valid_alerts_data_without_pagination(self, client, url_prefix, token, alerts):
        resp = client.post(url_prefix + '/alerts/data', headers={'x-access-token': token}, data={"source": self.source})
        assert resp.status_code == 200

        response_dict = json.loads(resp.data)
        assert response_dict['status'] == 'success'
        assert response_dict['data']['count'] == get_results_by_alert_source(start=0, limit=10, source=self.source)['count']

        assert response_dict['data']['results'] == get_results_by_alert_source(start=0, limit=10, source=self.source)['results']

    def test_valid_alerts_data_with_pagination(self, client, url_prefix, token, alerts):
        resp = client.post(url_prefix + '/alerts/data', headers={'x-access-token': token}, data=self.payload)
        assert resp.status_code == 200

        response_dict = json.loads(resp.data)
        if response_dict['data']:
            assert response_dict['status'] == 'success'
            assert response_dict['data'] == get_results_by_alert_source(
                self.start, self.limit, self.source)

            assert response_dict['data']['pagination'] == get_results_by_alert_source(
            self.start, self.limit, self.source)['pagination']

            assert response_dict['data']['data'] == get_results_by_alert_source(
            self.start, self.limit, self.source)['data']
        else:
            assert response_dict['status'] == 'failure'
            assert response_dict['data'] == []

    def test_alerts_data_without_source(self, client, url_prefix, token, alerts):
        resp = client.post(url_prefix + '/alerts/data', headers={'x-access-token': token}, data={})
        assert resp.status_code == 400
        response_dict = json.loads(resp.data)
        assert 'errors' in response_dict
        assert 'data' not in response_dict
        assert response_dict['message'] == 'Input payload validation failed'

    def test_alerts_data_invalid_url(self, client, url_prefix, token):
        resp = client.post(url_prefix + '/data', headers={'x-access-token': token}, data=self.payload)
        assert resp.status_code == 404


class TestGetAlertInvestigateData:

    def test_get_empty_data(self, client, url_prefix, token):
        resp = client.get(url_prefix + '/alerts/data/1', headers={'x-access-token': token})
        assert resp.status_code == 200
        response_dict = json.loads(resp.data)
        assert response_dict['status'] == 'failure'
        assert response_dict['data'] is None
        # alert = dao.get_alerts_by_alert_id(1)
        # assert response_dict['data'] == alerts_details(alert)

    def test_get_invalid_method(self, client, url_prefix, token):
        resp = client.post(url_prefix + '/alerts/data/1', headers={'x-access-token': token})
        assert resp.status_code == 405

    def test_get_invalid_url(self, client, url_prefix, token):
        resp = client.get(url_prefix + '/alert/data/1', headers={'x-access-token': token})
        assert resp.status_code == 404

    def test_get_data(self, client, url_prefix, token, alerts):
        resp = client.get(url_prefix + '/alerts/data/1', headers={'x-access-token': token})
        assert resp.status_code == 200
        response_dict = json.loads(resp.data)
        assert response_dict['status'] == 'success'
        alert = dao.get_alert_by_id(1)
        assert response_dict['data'] == alerts_details(alert)


class TestExportCsvAlerts:
    def test_export_csv_alerts_empty_data(self, client, url_prefix, token):
        resp = client.post(url_prefix + '/alerts/alert_source/export', headers={'x-access-token': token},
                           data={'source': 'alienvault'})
        assert resp.status_code == 200
        response_dict = json.loads(resp.data)
        assert response_dict is None

        """Test-case with payload """
        resp = client.post(url_prefix + '/alerts/alert_source/export', headers={'x-access-token': token})
        assert resp.status_code == 400

    def test_export_csv_invalid_url(self, client, url_prefix, token):
        resp = client.post(url_prefix + '/alert_source/export', headers={'x-access-token': token},
                           data={'source': 'rule'})
        assert resp.status_code == 404

    def test_export_csv_invalid_method(self, client, url_prefix, token):
        resp = client.get(url_prefix + '/alerts/alert_source/export', headers={'x-access-token': token},
                           data={'source': 'rule'})
        assert resp.status_code == 405

    def test_export_csv_alerts_with_data(self, client, url_prefix, token, alerts):
        resp = client.post(url_prefix + '/alerts/alert_source/export', headers={'x-access-token': token},
                           data={'source': 'virustotal'})
        assert resp.status_code == 200
        results = alerts_dao.get_alert_source('virustotal')
        if not results:
            response_dict = json.loads(resp.data)
            assert response_dict['status'] == 'failure'
            assert response_dict['message'] == "Data couldn't find for the alert source given!"
        else:
            assert resp.data == get_response(results).data

        """ Test-case without Payloads """
        resp = client.post(url_prefix + '/alerts/alert_source/export', headers={'x-access-token': token})
        assert resp.status_code == 400


class TestProcessAnalysisParentData:
    payload = {'process_guid': "CFA60AEC-1D78-11EA-9CAD-A4C3F0975828"}

    def test_get_empty_data(self, client, url_prefix, token):
        resp = client.post(
            url_prefix + '/alerts/data/process/1', headers={'x-access-token': token}, data={})
        assert resp.status_code == 400


    def test_get_invalid_method(self, client, url_prefix, token):
        resp = client.get(
            url_prefix + '/alerts/data/process/1', headers={'x-access-token': token}, data=self.payload)
        assert resp.status_code == 405

    def test_get_invalid_url(self, client, url_prefix, token):
        resp = client.post(
            url_prefix + '/alerts/data/process', headers={'x-access-token': token}, data=self.payload)
        assert resp.status_code == 404

    def test_get_data_without_child(self, client, url_prefix, token, alerts):
        resp = client.post(url_prefix + '/alerts/data/process/1', headers={'x-access-token': token}, data=self.payload)
        assert resp.status_code == 200
        response_dict = json.loads(resp.data)
        assert response_dict['status'] == 'success'
        alert = dao.get_alert_by_id(1)
        assert response_dict['data'] == graph_data_based_on_process(alert, self.payload['process_guid'])

    def test_get_data_with_child(self, client, url_prefix, token, alerts, result_log):
        resp = client.post(url_prefix + '/alerts/data/process/1', headers={'x-access-token': token},
                           data=self.payload)
        assert resp.status_code == 200
        response_dict = json.loads(resp.data)
        assert response_dict['status'] == 'success'
        alert = dao.get_alert_by_id(1)
        assert response_dict['data'] == graph_data_based_on_process(alert, self.payload['process_guid'])


class TestProcessAnalysisChildData:
    payload = {'alerted_action': 'FILE_RENAME', 'process_guid': 'CFA60AEC-1D78-11EA-9CAD-A4C3F0975828'}

    def test_get_empty_child_data(self, client, url_prefix, token):
        resp = client.post(
            url_prefix + '/alerts/data/process/child/1', headers={'x-access-token': token}, data=self.payload)
        assert resp.status_code == 200
        response_dict = json.loads(resp.data)
        assert response_dict['status'] == 'failure'
        assert response_dict['data'] == {}

    def test_get_invalid_method(self, client, url_prefix, token):
        resp = client.get(
            url_prefix + '/alerts/data/process/child/1', headers={'x-access-token': token}, data=self.payload)
        assert resp.status_code == 405

    def test_get_invalid_url(self, client, url_prefix, token):
        resp = client.get(
            url_prefix + '/data/process/child/1', headers={'x-access-token': token}, data=self.payload)
        assert resp.status_code == 404

    def test_get_data(self, client, url_prefix, token, alerts, result_log):
        resp = client.post(
            url_prefix + '/alerts/data/process/child/1', headers={'x-access-token': token}, data=self.payload)
        assert resp.status_code == 200
        response_dict = json.loads(resp.data)
        assert response_dict['status'] == 'success'
        alert = dao.get_alert_by_id(1)
        assert response_dict['data'] == child_node_data(alert, self.payload['process_guid'], self.payload['alerted_action'])


class TestRuleEndToEnd:
    def test_rule_end_to_end(self, client, url_prefix, token, app):
        from polylogyx.plugins import AbstractAlerterPlugin

        class DummyAlerter(AbstractAlerterPlugin):
            def __init__(self, *args, **kwargs):
                super(DummyAlerter, self).__init__(*args, **kwargs)
                self.calls = []

            def handle_alert(self, node, match, intel_match):
                self.calls.append((node, match))

        dummy_alerter = DummyAlerter()

        rule = Rule(name='DummyRule',
                    alerters=['dummy'],
                    description='',
                    conditions={
                        "condition": "AND",
                        "rules": [
                            {
                                "id": "query_name",
                                "field": "query_name",
                                "type": "string",
                                "input": "text",
                                "operator": "equal",
                                "value": "dummy-query"
                            }
                        ]
                    },
                    status='ACTIVE',
                    severity=Rule.WARNING, recon_queries=json.dumps(ALERT_RECON_QUERIES_JSON))
        rule.save()
        now = dt.datetime.utcnow()
        data = [
            {
                "diffResults": {
                    "added": [
                        {
                            "column_name": "column_value",
                        }
                    ],
                    "removed": ""
                },
                "name": "dummy-query",
                "hostIdentifier": "hostname.local",
                "calendarTime": "%s %s" % (now.ctime(), "UTC"),
                "unixTime": now.strftime('%s')
            }
        ]
        resp = client.post(url_prefix + '/alerts/data', headers={'x-access-token': token},
                           data={'source': 'rule'})
        assert resp.status_code == 200
        response_dict = json.loads(resp.data)
        # assert response_dict
