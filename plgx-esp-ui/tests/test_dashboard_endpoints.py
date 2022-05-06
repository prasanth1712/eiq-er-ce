import json

from polylogyx.blueprints.v1.utils import fetch_alert_node_query_status, fetch_dashboard_data


class TestDashboardData:

    def test_get_dashboard_empty_data(self, client, url_prefix, token):
        resp = client.get(url_prefix + '/dashboard', headers={'x-access-token': token})
        assert resp.status_code == 200
        response_dict = json.loads(resp.data)
        assert response_dict['status'] == 'success'
        alert_data = fetch_alert_node_query_status()
        distribution_and_status = fetch_dashboard_data()
        chart_data = {'alert_data': alert_data, 'distribution_and_status': distribution_and_status}
        assert response_dict['data'] == chart_data

    def test_get_invalid_method(self, client, url_prefix, token):
        resp = client.post(url_prefix + '/dashboard', headers={'x-access-token': token})
        assert resp.status_code == 405

    def test_get_invalid_url(self, client, url_prefix, token):
        resp = client.get(url_prefix + '/dashbord', headers={'x-access-token': token})
        assert resp.status_code == 404

    def test_get_dashboard_data(self, client, url_prefix, token, dashboard_data, alerts):
        resp = client.get(url_prefix + '/dashboard', headers={'x-access-token': token})
        assert resp.status_code == 200
        response_dict = json.loads(resp.data)
        assert response_dict['status'] == 'success'
        alert_data = fetch_alert_node_query_status()
        distribution_and_status = fetch_dashboard_data()
        chart_data={}
        chart_data['alert_data'] = alert_data
        chart_data['distribution_and_status'] = distribution_and_status
        assert response_dict['data'] == chart_data
