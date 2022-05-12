#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests, json
from flask import send_file, current_app
from flask_restplus import marshal
from polylogyx.blueprints.v1.utils import (
    get_host_id_by_node_id)
from polylogyx.dao.v1.hosts_dao import get_host_name_by_node_id
from polylogyx.dao.v1 import rules_dao, common_dao, hosts_dao, carves_dao
from polylogyx.models import db, Node, Tag, Alerts, Query, Pack, CarveSession, DistributedQueryTask
from polylogyx.wrappers.v1 import carve_wrappers as wrapper


class ApiError(Exception):
    pass


class BaseApiTest:
    """Base Api Test Class"""

    def __init__(self, base="https://localhost:5000/services/api/v1", username="admin", password="admin", proxies=None):
        """ sets variables including the headers """
        self.base = base
        self.username = username
        self.password = password
        self.proxies = proxies
        token = self.fetch_token()
        self.headers_post = {'x-access-token': token, 'content-type': 'application/json'}
        self.headers_get = {'x-access-token': token}
        self.headers_file = {'x-access-token': token}
        obj_utils = TestUtils()
        self.allNodes = obj_utils.get_list_of_all_host_ids()
        self.allQueries = obj_utils.get_list_of_all_queries()

    def fetch_token(self):
        """ fetches the token from the login api """

        url = self.base + '/login'
        request_data = {'username': self.username, 'password': self.password}
        try:
            r = requests.post(url, json=request_data, verify=False)
            response = self._return_response_and_status_code(r)
            if response['response_code'] == 200:
                return response['results']['token']
        except Exception as e:
            raise ApiError(e)

    def get_headers(self):
        return {'headers_post': self.headers_post, 'headers_get': self.headers_get, 'headers_file': self.headers_file}

    def get_request(self, url, payload=None, timeout=None):
        """ method to get the data from a url """

        try:
            if payload: response = requests.get(self.base + url, json=payload, proxies=self.proxies, timeout=timeout,headers=self.headers_get, verify=False)
            else: response = requests.get(self.base + url, proxies=self.proxies, timeout=timeout,headers=self.headers_get, verify=False)
        except requests.RequestException as e:
            return dict(error=str(e))

        return self.handle_response(response)

    def post_request(self, url, payload, timeout=None, files=None, is_multipart_form=False):
        """ method to post a data to the url for the payload given """

        try:
            if not is_multipart_form:
                response = requests.post(self.base + url, json=payload, proxies=self.proxies, timeout=timeout, headers=self.headers_post, verify=False)
            else:
                if payload:
                    response = requests.post(self.base + url, data=payload, proxies=self.proxies, timeout=timeout, headers=self.headers_file, verify=False, files=files)
                else:
                    response = requests.post(self.base + url, proxies=self.proxies, timeout=timeout,
                                                 headers=self.headers_file, verify=False, files=files)
        except requests.RequestException as e:
            return dict(error=str(e))

        return self.handle_response(response)

    def validate_status_code_and_success_status(self, result_response):
        assert int(result_response['response_code']) == 200 and 'results' in result_response
        assert result_response['results']['status'] == 'success'
        if 'data' in result_response['results']:
            if not result_response['results']['data']==None:
                if not len(result_response['results']['data']):
                    return None
                else:
                    return (True, result_response['results']['data'])
        else:
            return True

    def validate_status_code_and_failure_status(self, result_response):
        assert int(result_response['response_code']) == 200 and 'results' in result_response
        assert result_response['results']['status'] == 'failure'
        return True

    def handle_response(self, response):
        """ response will be returned to the call """
        return json.dumps(self._return_response_and_status_code(response=response))

    def _return_response_and_status_code(self, response, json_results=True):
        """ Output the requests response content or content as json and status code

        :rtype : dict
        :param response: requests response object
        :param json_results: Should return JSON or raw content
        :return: dict containing the response content and/or the status code with error string.
        """
        if response.status_code == requests.codes.ok:
            return dict(results=response.json() if json_results else response.content,
                        response_code=response.status_code)
        elif response.status_code == 400:
            return dict(
                error='package sent is either malformed or not within the past 24 hours.',
                response_code=response.status_code)
        elif response.status_code == 204:
            return dict(
                error='You exceeded the public API request rate limit (4 requests of any nature per minute)',
                response_code=response.status_code)
        elif response.status_code == 403:
            return dict(
                error='You tried to perform calls to functions for which you require a Private API key.',
                response_code=response.status_code)
        elif response.status_code == 404:
            return dict(error='File not found.', response_code=response.status_code)
        else:
            return dict(response_code=response.status_code)


class TestUtils:

    def get_list_of_all_host_ids(self):
        return list(db.session.query(Node.host_identifier).all())

    def get_list_of_all_tags(self):
        return list(db.session.query(Tag.value).all())

    def get_list_of_all_queries(self):
        return list(db.session.query(Query.name).all())

    def get_list_of_all_sql_raw_queries(self):
        return list(db.session.query(Query.sql).all())

    def get_an_existing_alert_input_data(self):
        data = db.session.query(Alerts.query_name, Alerts.node_id, Alerts.rule_id, Alerts.id).filter(Alerts.type=='rule').first()
        if data: return {'query_name':data[0], 'host_identifier':get_host_id_by_node_id(data[1]), 'rule_id':data[2], 'id':data[3], 'rule_name': rules_dao.get_rule_name_by_id(data[2])}
        else: return False

    def get_carve(self):
        carves = marshal(carves_dao.get_carves_all().offset(0).limit(10).all(), wrapper.carves_wrapper)
        total_count = carves_dao.get_carves_all().count()
        for carve in carves:
            carve['hostname'] = get_host_name_by_node_id(carve['node_id'])
        carves = {'count': total_count, 'results': carves}
        return carves

    def get_carves_with_host_identifier(self, host_identifier):
        node = hosts_dao.get_node_by_host_identifier(host_identifier)
        if node:
            carves = marshal(carves_dao.get_carves_by_node_id(node.id).offset(0).limit(100).all(),
                             wrapper.carves_wrapper)
            total_count = carves_dao.get_carves_by_node_id(node.id).count()
            for carve in carves:
                carve['hostname'] = get_host_name_by_node_id(carve['node_id'])
            carves = {'count': total_count, 'results': carves}
            return carves

    def get_query_dict(self):
        data = [query_obj.to_dict() for query_obj in db.session.query(Query).filter(Query.id==1).all()][0]
        if data: return {'name':data['name'], 'id':data['id'], 'sql':data['query']}
        else: return False

    def get_pack(self):
        data = [query_obj.to_dict() for query_obj in db.session.query(Pack).filter(Pack.id==1).all()][0]
        if data: return {'name':data['name'], 'id':data['id']}
        else: return False

    def get_carves_file(self, session_id):
        carve_session = carves_dao.get_carves_by_session_id(session_id)
        if carve_session:
            data = send_file(
                current_app.config[
                    'CARVES_URL'] + '/' + carve_session.node.host_identifier + '/' + carve_session.archive,
                as_attachment=True, mimetype='application/x-tar',
                attachment_filename='carve_session.tar'
            )
            data.direct_passthrough = False
            return data

    def get_carve_session_by_query_id(self, query_id, host_identifier):
        node = hosts_dao.get_node_by_host_identifier(host_identifier)
        if node:
            dqt = db.session.query(DistributedQueryTask).filter(
                DistributedQueryTask.distributed_query_id == query_id).filter(
                DistributedQueryTask.node_id == node.id).first()
            if dqt:
                carve_session = db.session.query(CarveSession).filter(
                    CarveSession.request_id == dqt.guid).first()
                if carve_session:
                    return marshal(carve_session, wrapper.carves_wrapper)
        return

    def get_hunt_data(self, lines, type, host_identifier=None, query_name=None):
        if not host_identifier:
            output_dict_data = {}
            hunt_search_results = common_dao.result_log_query_count(lines, type)
            for search_result in hunt_search_results:
                host_identifier = get_host_id_by_node_id(search_result[0])
                if not host_identifier in output_dict_data:
                    output_dict_data[host_identifier] = []
                output_dict_data[host_identifier].append({"query_name": search_result[1], "count": search_result[2]})
            data = output_dict_data
            if not output_dict_data:
                data = {}
        else:
            if query_name:
                try:
                    results = common_dao.result_log_query(lines, 'md5', 0, 10)
                except Exception as e:
                    results = None
                data = [result[2] for result in results if (get_host_id_by_node_id(result[0]) == 'foobar' and
                                                            result[1] == query_name)]
            else:
                data = None
        return data
