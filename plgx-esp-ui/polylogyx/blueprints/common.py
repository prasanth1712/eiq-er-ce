from io import BytesIO
import unicodecsv as csv
from operator import itemgetter
import jwt, json

from flask import jsonify, request, send_file, current_app
from flask_restplus import Namespace, Resource, marshal

from polylogyx.dao import common_dao as dao
from polylogyx.blueprints.utils import *
from polylogyx.utils import require_api_key
from polylogyx.wrappers import parent_wrappers as parentwrapper
from polylogyx.extensions import bcrypt
from polylogyx.models import ThreatIntelCredentials, User


ns = Namespace('common_api', description='all normal purpose apis operations', path = '/')


@require_api_key
@ns.route('/changepw', endpoint='change_password')
@ns.doc(params = {'old_password':"old password", 'new_password':"new password", 'confirm_new_password':"confirm new password"})
class ChangePassword(Resource):
    """changes user password"""
    parser = requestparse(['old_password', 'new_password', 'confirm_new_password'], [str, str, str], ["old password", "new password", "confirm new password"])

    @ns.expect(parser)
    def post(self):
        args = self.parser.parse_args()
        status = "failure"
        payload = jwt.decode(request.headers.environ.get('HTTP_X_ACCESS_TOKEN'), current_app.config['SECRET_KEY'])
        user = User.query.filter_by(id=payload['id']).first()
        if args['new_password']==args['confirm_new_password']:
            if bcrypt.check_password_hash(user.password, args['old_password']):
                current_app.logger.info("%s has changed password and the old password and new passwords are %s and %s", user.username, args['old_password'], args['new_password'])
                user.update(password=bcrypt.generate_password_hash(args['new_password'].encode("utf-8")).decode("utf-8"))
                message = "password is updated successfully"
                status = "success"
            else:
                message = "old password is not matching"
        else:
            message = "new password and confirm new password are not matching for the user"
        return marshal(prepare_response(message,status),parentwrapper.common_response_wrapper,skip_none=True)


@require_api_key
@ns.route('/options/add', endpoint = "add_options")
@ns.doc(params = {'option':"option data", 'name':"name for the option"})
class AddOption(Resource):
    """Add Options"""
    parser = requestparse(['option'],[dict],["option data"],[True])

    @ns.expect(parser)
    def post(self):
        args = self.parser.parse_args()
        data = None
        existing_option = dao.options_query()
        options = args['option']

        for k, v in options.items():
            option = dao.options_filter_by_key(k)
            if option:
                option.option = v
                option.update(option)
            else:
                dao.create_option(k,v)
        if existing_option:
            #convert json into unicode or string format as options db column is string only
            existing_option.option = json.dumps(args['option'])
            existing_option.update(options)
            data = json.loads(existing_option.option)
        else:
            # convert json into unicode or string format as options db column is string only
            option = dao.create_option_by_option(json.dumps(args['option']))
            data = json.loads(option.option)
        if not data: message = "options you updated are null and no data exists to show"
        return marshal(prepare_response("options are updated successfully","success",data),parentwrapper.common_response_wrapper,skip_none=True)


@require_api_key
@ns.route('/hunt-upload', endpoint="hunt_file_upload")
class FileUpload(Resource):
    """hunt file upload"""

    from werkzeug import datastructures
    parser = requestparse(['file', 'type', 'host_identifier', "query_name", "start", "limit"],
                          [datastructures.FileStorage, str, str, str, int, int],
                          ['Threat file', 'type of threat (md5/sha256)', 'host_identifier of the node', "query_name",
                           "start", "limit"], [True, True, False, False, False, False])

    @ns.expect(parser)
    def post(self):
        import os
        args = self.parser.parse_args()
        data = None
        status = "failure"
        message = None

        type = args['type']
        file = args['file']
        query_name = args['query_name']
        host_identifier = args['host_identifier']
        start = args['start']
        limit = args['limit']
        if not start:
            start = 0
        if not limit:
            limit = 100

        lines = [line.decode('utf-8').replace('\n', '') for line in file.readlines()]

        if not host_identifier:
            output_dict_data={}
            hunt_search_results = dao.result_log_query_count(lines, type)
            for search_result in hunt_search_results:
                host_identifier = get_host_id_by_node_id(search_result[0])
                if not host_identifier in output_dict_data:
                    output_dict_data[host_identifier] = []
                output_dict_data[host_identifier].append({"query_name": search_result[1], "count": search_result[2]})

            if output_dict_data:
                message = "successfully fetched the data through the hunt file uploaded"
            else:
                message = "No matching results found"
            status = "success"
            data = output_dict_data

        else:
            if not query_name:
                message = "please provide the query name"
            else:
                try:
                    results = dao.result_log_query(lines, type, start, limit)
                except Exception as e:
                    results = None
                    message = str(e)
                data = [result[2] for result in results if (
                        get_host_id_by_node_id(result[0]) == host_identifier and result[1] == query_name)]
        if not data and not message:
            message = "no matching data found"
        elif data:
            message = "successfully fetched the data through the hunt file uploaded"
            status = "success"

        return marshal(prepare_response(message, status, data), parentwrapper.common_response_wrapper, skip_none=True)


@require_api_key
@ns.route('/search', endpoint="search")
@ns.doc(params={})
class Search(Resource):
    """ Search Operation """
    parser = requestparse(['conditions', 'host_identifier', 'query_name', 'start', 'limit'], [dict, str, str, int, int],
                          ["conditions to search for", 'host_identifier of the node', 'query_name', 'start', 'limit'],
                          [True, False, False, False, False])

    @ns.expect(parser)
    def post(self):
        args = self.parser.parse_args()
        host_identifier = args['host_identifier']
        query_name = args['query_name']
        start = args['start']
        limit = args['limit']
        conditions = args['conditions']
        if not start:
            start = 0
        if not limit:
            limit = 100

        data = None
        status = "failure"
        message = None
        try:
            search_rules = SearchParser()
            root = search_rules.parse_group(conditions)
        except Exception as e:
            message = str(e)
            return marshal(prepare_response(message, status),
                           parentwrapper.common_response_wrapper, skip_none=True)

        try:
            filter = root.run('', [], 'result_log')
        except Exception as e:
            message = str(e)
        output_dict_data = {}

        if not host_identifier:
            search_results = dao.result_log_search_results_count(filter)
            for search_result in search_results:
                host_identifier = get_host_id_by_node_id(search_result[0])
                if not host_identifier in output_dict_data:
                    output_dict_data[host_identifier]=[]
                output_dict_data[host_identifier].append({"query_name": search_result[1], "count": search_result[2]})

            message = "successfully fetched the data through the payload given"
            status = "success"
            data = output_dict_data

        else:
            if not query_name:
                message = "please provide the query name"
            else:
                data = dao.result_log_search_results(filter, get_node_id_by_host_id(host_identifier),query_name, start, limit )
                data=[data_elem[0] for data_elem  in data]
        if not data and not message:
            message = "no matching data found"
        elif data:
            message = "successfully fetched the data through the payload given"
            status = "success"

        return marshal(prepare_response(message, status, data), parentwrapper.common_response_wrapper, skip_none=True)


@require_api_key
@ns.route('/queryresult/delete', endpoint = "delete_queryresult")
@ns.doc(params = {'days_of_data':"no.of days of data to delete"})
class DeleteQueryResult(Resource):
    """Deleting the scheduled query result will be done here"""
    parser = requestparse(['days_of_data'],[int],["no.of days of data to delete"])

    def func(self):
        args = self.parser.parse_args()
        since = dt.datetime.now() - dt.timedelta(hours=24 * int(args['days_of_data']))
        dao.del_result_log_obj(since)
        db.session.commit()
        return marshal(prepare_response("query result data is deleted successfully","success"),parentwrapper.common_response_wrapper,skip_none=True)

    @ns.expect(parser)
    def post(self):
        return self.func()


@require_api_key
@ns.route('/queryresult/<int:days_of_data>', endpoint = "preview_queryresult")
@ns.doc(params = {'days_of_data':"no.of days of data to preview"})
class PreviewQueryResult(Resource):
    """Previewing the scheduled query result will be done here"""

    def get(self, days_of_data=None):
        from polylogyx.wrappers import resultlog_wrappers
        since = dt.datetime.now() - dt.timedelta(hours=24 * int(days_of_data))
        data = marshal(dao.get_result_log_since(since), resultlog_wrappers.result_log_wrapper)
        message = "The following is the data we have received since the no.of days you passed"
        status = "success"
        if not data:
            message = "there is no data display, its empty!"
            status = "failure"
        return marshal(prepare_response(message, status, data),
                       parentwrapper.common_response_wrapper, skip_none=True)



@require_api_key
@ns.route('/schedule_query/export', endpoint="schedule_query_export")
@ns.doc(params = {})
class ExportScheduleQueryCSV(Resource):
    """exports schedule query results into a csv file"""
    parser = requestparse(['query_name', 'host_identifier'], [str, str], ["name of the query", "host identifier of the node"])

    @ns.expect(parser)
    def post(self):
        all_args = self.parser.parse_args()

        query_name = all_args['query_name']
        host_identifier = all_args['host_identifier']
        node_id = get_node_id_by_host_id(host_identifier)

        record_query = dao.record_query(node_id,query_name)

        results = [r for r, in record_query]
        headers = []
        if not len(results)==0:
            firstRecord = results[0]
            for key in firstRecord.keys():
                headers.append(key)

        bio = BytesIO()
        writer = csv.writer(bio)
        writer.writerow(headers)

        for data in results:
            row = []
            row.extend([data.get(column, '') for column in headers])
            writer.writerow(row)

        bio.seek(0)

        file_data = send_file(
            bio,
            mimetype='text/csv',
            as_attachment=True,
            attachment_filename='query_results.csv'
        )
        return file_data

@require_api_key
@ns.route('/nodes_csv')
@ns.doc(params = {})
class NodesCSV(Resource):
    """returns a csv file object with nodes info as data"""
    def get(self):
        headers = [
            'Display name',
            'Host identifier',
            'Enrolled On',
            'Last Check-in',
            'Last IP Address',
            'Is Active',
        ]

        column_names = map(itemgetter(0), current_app.config['POLYLOGYX_CAPTURE_NODE_INFO'])
        labels = map(itemgetter(1), current_app.config['POLYLOGYX_CAPTURE_NODE_INFO'])
        headers.extend(labels)
        headers = list(map(str.title, headers))

        bio = BytesIO()
        writer = csv.writer(bio)
        writer.writerow(headers)

        for node in Node.query:
            row = [
                node.display_name,
                node.host_identifier,
                node.enrolled_on,
                node.last_checkin,
                node.last_ip,
                node.is_active,
            ]
            row.extend([node.node_info.get(column, '') for column in column_names])
            writer.writerow(row)

        bio.seek(0)

        file_data = send_file(
            bio,
            mimetype='text/csv',
            as_attachment=True,
            attachment_filename='nodes.csv'
        )
        return file_data


@require_api_key
@ns.route('/apikeys', endpoint='add_apikey')
@ns.doc(params = {'vt_key':"vt key",'IBMxForceKey':"IBMxForceKey",'IBMxForcePass':"IBMxForcePass",'otx_key':"otx_key"})
class UpdateApiKeys(Resource):
    """adds API keys"""
    parser = requestparse(['vt_key', 'IBMxForceKey', 'IBMxForcePass','otx_key'], [str, str, str,str],
                          ['vt key', 'IBMxForceKey', 'IBMxForcePass','otx key'],[False,False,False,False])

    def func(self):
        args = self.parser.parse_args()
        vt_key = args['vt_key']
        ibm_key = args['IBMxForceKey']
        ibm_pass = args['IBMxForcePass']
        otx_key = args['otx_key']

        error_message=None
        if ibm_key and ibm_pass:
            ibm_x_force_credentials=db.session.query(ThreatIntelCredentials).filter(ThreatIntelCredentials.intel_name=='ibmxforce').first()

            if ibm_x_force_credentials:
                new_credentials = dict(ibm_x_force_credentials.credentials)
                new_credentials['key'] = ibm_key
                new_credentials['pass'] = ibm_pass
                ibm_x_force_credentials.credentials = new_credentials
                db.session.add(ibm_x_force_credentials)
                db.session.commit()
            else:
                credentials={}
                credentials['key']=ibm_key
                credentials['pass']=ibm_pass
                ThreatIntelCredentials.create(intel_name='ibmxforce', credentials=credentials)

        if vt_key:
            vt_credentials = db.session.query(ThreatIntelCredentials).filter(
                ThreatIntelCredentials.intel_name == 'virustotal').first()

            if vt_credentials:
                new_credentials = dict(vt_credentials.credentials)
                new_credentials['key'] = vt_key
                vt_credentials.credentials = new_credentials
                db.session.add(vt_credentials)
                db.session.commit()
            else:
                credentials = {}
                credentials['key'] = vt_key
                ThreatIntelCredentials.create(intel_name='virustotal', credentials=credentials)
        if otx_key:
            alienvault_credentials = db.session.query(ThreatIntelCredentials).filter(
                ThreatIntelCredentials.intel_name == 'alienvault').first()

            if alienvault_credentials:
                new_credentials = dict(alienvault_credentials.credentials)
                new_credentials['key'] = otx_key
                alienvault_credentials.credentials = new_credentials
                db.session.add(alienvault_credentials)
                db.session.commit()
            else:
                credentials = {}
                credentials['key'] = otx_key
                ThreatIntelCredentials.create(intel_name='alienvault', credentials=credentials)


        API_KEYS = {}
        threat_intel_credentials = ThreatIntelCredentials.query.all()
        for threat_intel_credential in threat_intel_credentials:
            API_KEYS[threat_intel_credential.intel_name] = threat_intel_credential.credentials
        if not API_KEYS: message = "Api keys data doesn't exists"
        return marshal(prepare_response("API keys were updated successfully","success",API_KEYS),parentwrapper.common_response_wrapper,skip_none=True)

    @ns.expect(parser)
    def post(self):
        return self.func()

    def get(self):
        API_KEYS = {}
        threat_intel_credentials = ThreatIntelCredentials.query.all()
        for threat_intel_credential in threat_intel_credentials:
            API_KEYS[threat_intel_credential.intel_name] = threat_intel_credential.credentials
        if not API_KEYS: message = "Api keys data doesn't exists"
        return marshal(prepare_response("API keys were fetched successfully","success",API_KEYS),parentwrapper.common_response_wrapper,skip_none=True)

