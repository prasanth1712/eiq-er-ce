import re

from flask_restplus import Namespace, Resource, inputs
from flask import json

from polylogyx.blueprints.v1.utils import *
from polylogyx.util.mitre import MitreApi
from polylogyx.dao.v1 import rules_dao
from polylogyx.wrappers.v1 import rule_wrappers, parent_wrappers
from polylogyx.authorize import admin_required

ns = Namespace('rules', description='rules related operations')


def validate_technique_id(technique_id):
    for value in technique_id:
        if not re.search("^(T1)\d{3}$", value):
            return False
    return True


@ns.route('', endpoint="list rules")
class RuleList(Resource):
    """
        Lists all Rules
    """
    parser = requestparse(["start", "limit", "searchterm", 'alerts_count'], [int, int, str, inputs.boolean],
                          ["start", "limit", "searchterm", 'alerts_count(true/false)'], [False, False, False, False],
                          [None, None, None, None], [None, None, '', True])

    @ns.expect(parser)
    @ns.marshal_with(parent_wrappers.common_response_wrapper)
    def post(self):
        args = self.parser.parse_args()
        query_set = rules_dao.get_all_rules(args['searchterm'], args['alerts_count']).offset(args['start'])\
            .limit(args['limit']).all()
        data = []
        for rule_alerts_count_pair in query_set:
            if args['alerts_count']:
                rules = rule_alerts_count_pair[0]
            else:
                rules = rule_alerts_count_pair
            rule_dict = marshal(rules, rule_wrappers.rule_wrapper)
            if args['alerts_count']:
                rule_dict['alerts_count'] = rule_alerts_count_pair[1]
            data.append(rule_dict)
        message = "Successfully fetched the rules info"
        status = "success"
        response = {'count': rules_dao.get_all_rules(args['searchterm'], args['alerts_count']).count(),
                    'total_count': rules_dao.get_total_count(), 'results': data,
                    'total_alerts': rules_dao.get_rule_alerts_count()}
        return prepare_response(message, status, response)


@ns.route('/<int:rule_id>', endpoint="list rule by id")
class GetRuleById(Resource):
    """
        Lists the rule by its ID
    """

    def get(self, rule_id):
        if rule_id:
            rule = rules_dao.get_rule_by_id(rule_id)
            if rule:
                data = marshal(rule, rule_wrappers.rule_wrapper)
                return prepare_response("Successfully fetched the rules info", "success", data)
            else:
                message = "Rule with this id does not exist"
        else:
            message = "Missing rule id"
        return marshal(prepare_response(message), parent_wrappers.failure_response_parent)


@ns.route('/<int:rule_id>', endpoint="edit rule by id")
class ModifyRuleById(Resource):
    """
        Modifies the rule data for the passed rule_id
    """
    parser = requestparse(['alerters', 'name', 'description', 'conditions', 'recon_queries', 'severity', 'status',
                           'type', 'tactics', 'technique_id', 'platform', 'alert_description'],
                          [str, str, str, dict, list, str, str, str, str, str, str, inputs.boolean],
                          ["alerters", "name of the rule", "description of the rule", "conditions", "recon_queries",
                           "severity", 'status', 'type', 'tactics', 'technique_id', 'platform', 'alert_description'],
                          [False, True, False, True, False, False, False, False, False, False, False, False],
                          [None, None, None, None, None, ["WARNING", "INFO", "CRITICAL"],
                           None, None, None, None, None, None],
                          [None, None, None, None, None, None, None, None, None, None, 'all', False])

    @admin_required
    @ns.expect(parser)
    def post(self, rule_id):
        args = self.parser.parse_args()

        if rule_id:
            rule = rules_dao.get_rule_by_id(rule_id)
            if rule:
                alerters = []
                if args['alerters']:
                    alerters = args['alerters'].split(',')
                name = args['name']
                description = args['description']
                conditions = args['conditions']
                recon_queries = args['recon_queries']
                severity = args['severity']
                type_ip = args['type']
                tactics = args['tactics']
                platform = args['platform']

                if tactics:
                    tactics = tactics.split(',')
                else:
                    tactics = []
                if args['technique_id']:
                    technique_id = args['technique_id'].split(',')
                else:
                    technique_id = []

                existing_rule_by_name = rules_dao.get_rule_by_name(name)
                if existing_rule_by_name and existing_rule_by_name.id != rule.id:
                    message = "Rule with the name {0} already exists!".format(name)
                elif technique_id and not validate_technique_id(technique_id):
                    message = "Technique id provided is invalid, please provide exact technique id"
                else:
                    if alerters is None:
                        alerters = []
                    if 'debug' not in alerters:
                        alerters.append('debug')
                    rule_status = rule.status
                    if args['status']:
                        rule_status = args['status']
                    try:
                        rules = RuleParser()
                        root = rules.parse_group(conditions)
                    except Exception as e:
                        return marshal(prepare_response(str(e), "failure"), parent_wrappers.failure_response_parent)

                    rule = rules_dao.edit_rule_by_id(rule_id, name, alerters, description, conditions, rule_status,
                                                     dt.datetime.utcnow(), json.dumps(recon_queries), severity, type_ip,
                                                     tactics, args['technique_id'], platform, args['alert_description'])
                    current_app.logger.info("Rule '{0}' has been updated with given payload".format(rule))
                    return prepare_response("Successfully modified the rules info", "success",
                                            marshal(rule, rule_wrappers.rule_wrapper))
            else:
                message = "Rule with this id does not exist"
        else:
            message = "Missing rule id"
        return marshal(prepare_response(message), parent_wrappers.failure_response_parent)


@ns.route('/add', endpoint="add rule")
class AddRule(Resource):
    """
        Adds and returns the API response if there is any existed data for the passed rule_id
    """
    parser = requestparse(['alerters', 'name', 'description', 'conditions', 'recon_queries', 'severity', 'status',
                           'type', 'tactics', 'technique_id', 'platform', 'alert_description'],
                          [str, str, str, dict, list, str, str, str, str, str, str, inputs.boolean],
                          ["alerters", "name of the rule", "description of the rule", "conditions", "recon_queries",
                           "severity", 'status', 'type', 'tactics', 'technique_id', 'platform', 'alert_description'],
                          [False, True, False, True, False, False, False, False, False, False, False, False],
                          [None, None, None, None, None, ["WARNING", "INFO", "CRITICAL"], None,
                           None, None, None, None, None],
                          [None, None, None, None, None, None, None, None, None, None, 'all', False])

    @admin_required
    @ns.expect(parser)
    def post(self):
        from polylogyx.models import Rule
        args = self.parser.parse_args()
        alerters = []
        if args['alerters']:
            alerters = args['alerters'].split(',')
        name = args['name']
        description = args['description']
        conditions = args['conditions']
        recon_queries = args['recon_queries']
        severity = args['severity']
        platform = args['platform']

        if not severity:
            severity = Rule.INFO

        type_ip = args['type']
        tactics = args['tactics']
        if tactics:
            tactics = tactics.split(',')
        else:
            tactics = []
        if args['technique_id']:
            technique_id = args['technique_id'].split(',')
        else:
            technique_id = []
        status = args['status']

        existing_rule = rules_dao.get_rule_by_name(name)
        if existing_rule:
            message = u"Rule with the name {0} already exists!".format(name)
        elif technique_id and not validate_technique_id(technique_id):
            message = "Technique id(s) provided is invalid, please provide valid technique id"
        else:
            try:
                rules = RuleParser()
                root = rules.parse_group(conditions)
            except Exception as e:
                current_app.logger.error("Unable to add rule - {}".format(str(e)))
                return marshal(prepare_response(str(e), "failure"), parent_wrappers.failure_response_parent)
            if not status:
                status = "ACTIVE"
            if alerters is None:
                alerters = []
            if 'debug' not in alerters:
                alerters.append('debug')
            rule = rules_dao.create_rule_object(name, alerters, description, conditions, status, type_ip, tactics,
                                                args['technique_id'], json.dumps(recon_queries),
                                                severity, platform, args['alert_description'])
            rule.save()
            current_app.logger.info("A new Rule '{0}' has been added with given payload".format(rule))
            return marshal({'message': "Rule is added successfully", 'status': "success", 'rule_id': rule.id},
                           rule_wrappers.response_add_rule)
        return marshal(prepare_response(message), parent_wrappers.failure_response_parent)


@ns.route('/tactics', endpoint="get tactics by technique ids")
class GetTactics(Resource):
    """
        Gets tactics for technique id
    """
    parser = requestparse(['technique_ids'], [str], ["technique_ids"], [True])

    @ns.expect(parser)
    def post(self):
        args = self.parser.parse_args()
        mitre_api = MitreApi()
        technique_id = args["technique_ids"]
        tactics_with_description = mitre_api.get_tactics_by_technique_id(technique_id.split(","))
        return marshal(prepare_response("Tactics are fetched successfully from technique ids", "success",
                                        tactics_with_description), parent_wrappers.common_response_wrapper)
