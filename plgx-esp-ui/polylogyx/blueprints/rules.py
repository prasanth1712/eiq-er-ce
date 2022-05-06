import json
import datetime as dt
import re

from flask import jsonify, request
from flask_restplus import Namespace, Resource, marshal

from .utils import *
from polylogyx.utils import require_api_key
from polylogyx.dao import rules_dao as dao
from polylogyx.wrappers import rule_wrappers as wrapper
from polylogyx.wrappers import parent_wrappers as parentwrapper


ns = Namespace('rules', description='rules related operations')


def validate_technique_id(technique_id):
    if re.search("^(T1)\d{3}$",technique_id): return True
    else: return False


@require_api_key
@ns.route('/', endpoint = "list_rules")
@ns.doc(params = {})
class RuleList(Resource):
    """Lists all Rules"""
    @ns.marshal_with(wrapper.common_response_wrapper)
    def get(self):
        #data = [rule.as_dict() for rule in dao.getAllRules()]
        data = marshal(dao.get_all_rules(), wrapper.rule_wrapper)
        message = "successfully fetched the rules info"
        if not data: message = "there is no data to be shown"
        return prepare_response(message,"success",data)


@require_api_key
@ns.route('/<int:rule_id>', endpoint = "list_rule_by_id")
@ns.doc(params = {'rule_id':"id of the rule"})
class GetRuleById(Resource):
    """Lists the rule by its ID"""

    def get(self, rule_id):
        if rule_id:
            rule = dao.get_rule_by_id(rule_id)
            if rule:
                #data = rule.as_dict()
                data = marshal(rule, wrapper.rule_wrapper)
                return prepare_response("successfully fetched the rules info","success",data)
            else:
                message="Rule with this id does not exist"
        else:
            message = "Missing rule id"
        return marshal(prepare_response(message), parentwrapper.failure_response_parent)


@require_api_key
@ns.route('/<int:rule_id>', endpoint = "edit_rule_by_id")
@ns.doc(params = {'rule_id':"id of the rule", 'alerters':"alerters", 'name': "name of the rule", 'description':"description of the rule", 'conditions':"conditions", 'recon_queries':"recon_queries", 'severity':"severity", 'status':"status"})
class ModifyRuleById(Resource):
    """modifies the rule data for the passed rule_id"""
    parser = requestparse(['alerters', 'name', 'description', 'conditions', 'recon_queries', 'severity', 'status', 'type', 'tactics', 'technique_id'],[str, str, str, dict, list, str, str, str, str, str],["alerters", "name of the rule", "description of the rule", "conditions", "recon_queries","severity", 'status', 'type', 'tactics', 'technique_id'], [False, True, True, True, False, False, False, False, False, False])

    @ns.expect(parser)
    def post(self, rule_id):
        args = self.parser.parse_args()  # need to exists for input payload validation

        if rule_id:
            rule = dao.get_rule_by_id(rule_id)
            if rule:
                alerters = args['alerters'].split(',')
                name = args['name']
                description = args['description']
                conditions = args['conditions']
                recon_queries = args['recon_queries']
                severity = args['severity']
                type_ip = args['type']
                tactics = args['tactics']
                if tactics: tactics=tactics.split(',')
                technique_id = args['technique_id']

                existing_rule_by_name = dao.get_rule_by_name(name)
                if existing_rule_by_name and existing_rule_by_name.id != rule.id:
                    message = "Rule with the name {0} already exists!".format(name)

                elif technique_id and not validate_technique_id(technique_id):
                    message = "technique id provided is invalid, please provide exact technique id"

                else:
                    if alerters is None:
                        alerters = []
                    if not 'debug' in alerters:
                        alerters.append('debug')
                    rule_status = rule.status
                    if args['status']:
                        rule_status = args['status']

                    rule = dao.edit_rule_by_id(rule_id,name,alerters,description,conditions,rule_status,dt.datetime.utcnow(),json.dumps(recon_queries),severity,type_ip,tactics,technique_id)

                    return prepare_response("Successfully modified the rules info","success",marshal(rule, wrapper.rule_wrapper))
            else:
                message = "rule with this id does not exist"
        else:
            message="Missing rule id"
        return marshal(prepare_response(message), parentwrapper.failure_response_parent)


@require_api_key
@ns.route('/add', endpoint = "add_rule")
@ns.doc(params = {'alerters':"alerters", 'name': "name of the rule", 'description':"description of the rule", 'conditions':"conditions", 'recon_queries':"recon_queries", 'severity':"severity", 'status':"status",'type':"type",'tactics':"tactics",'technique_id':"technique_id"})
class AddRule(Resource):
    """adds and returns the API response if there is any existed data for the passed rule_id"""
    parser = requestparse(['alerters', 'name', 'description', 'conditions', 'recon_queries', 'severity', 'status', 'type', 'tactics', 'technique_id'],[str, str, str, dict, list, str, str, str, str, str],["alerters", "name of the rule", "description of the rule", "conditions", "recon_queries", "severity", 'status', 'type', 'tactics', 'technique_id'], [False, True, True, True, False, False, False, False, False, False])

    @ns.expect(parser)
    def post(self):
        from polylogyx.models import Rule
        args = self.parser.parse_args()  # need to exists for input payload validation

        alerters = args['alerters'].split(',')
        name = args['name']
        description = args['description']
        conditions = args['conditions']
        recon_queries = args['recon_queries']
        severity = args['severity']

        if not severity: severity=Rule.INFO

        type_ip = args['type']
        tactics = args['tactics']
        if tactics: tactics = tactics.split(',')
        technique_id = args['technique_id']
        status = args['status']

        existing_rule = dao.get_rule_by_name(name)
        if existing_rule:
            message = u"Rule with the name {0} already exists!".format(name)
        elif technique_id and not validate_technique_id(technique_id):
            message = "technique id provided is invalid, please provide exact technique id"
        else:
            try:
                parse_group(conditions)
            except Exception as e:
                return marshal(prepare_response(str(e), "failure"),parentwrapper.failure_response_parent)
            if not status:
                status = "ACTIVE"
            if alerters is None:
                alerters = []
            if not 'debug' in alerters:
                alerters.append('debug')
            rule = dao.create_rule_object(name,alerters,description,conditions,status,type_ip,tactics,technique_id,dt.datetime.utcnow(),json.dumps(recon_queries),severity)
            rule.save()
            return marshal({'message': "rule is added successfully", 'status':"success",'rule_id': rule.id}, wrapper.response_add_rule)
        return marshal(prepare_response(message), parentwrapper.failure_response_parent)

