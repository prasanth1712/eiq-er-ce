from flask_restplus import fields
import datetime
from polylogyx.blueprints.v1.external_api import api

rule_wrapper = api.model('rule_info', {
    'id': fields.Integer(),
    'alerters': fields.List(fields.String(default=None)),
    'conditions': fields.Raw(default=None),
    'description': fields.String(default=None),
    'name': fields.String(default=None),
    'severity': fields.String(default=None),
    'platform': fields.String(default=None),
    'status': fields.String(default=None),
    'updated_at': fields.DateTime(default=datetime.datetime.now()),
    'type': fields.String(default=None),
    'tactics': fields.Raw(),
    'technique_id': fields.String(default=None),
    'alert_description': fields.Boolean(default=None)
})


response_add_rule = api.model('rule_add_wrapper', {
    'status': fields.String(default="success"),
    'rule_id': fields.Integer(),
    'message': fields.String(default='rule is added successfully')
})
