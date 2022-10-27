from flask_restful import fields
import datetime
from polylogyx.blueprints.v1.external_api import api

rule_wrapper =  {
    'id': fields.Integer(),
    'alerters': fields.List(fields.String(default=None)),
    'conditions': fields.Raw(default=None),
    'description': fields.String(default=None),
    'name': fields.String(default=None),
    'severity': fields.String(default=None),
    'platform': fields.String(default=None),
    'status': fields.String(default=None),
    'created_at':fields.String(default=datetime.datetime.now().strftime('%d-%m-%Y %H:%M:%S')),
    'updated_at': fields.String(default=datetime.datetime.now().strftime('%d-%m-%Y %H:%M:%S')),
    'type': fields.String(default=None),
    'tactics': fields.Raw(),
    'technique_id': fields.String(default=None),
    'alert_description': fields.Boolean(default=None)
}


response_add_rule = {
    'status': fields.String(default="success"),
    'rule_id': fields.Integer(),
    'message': fields.String(default='rule is added successfully')
}
