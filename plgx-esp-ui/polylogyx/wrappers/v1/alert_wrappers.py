from flask_restful import fields
from polylogyx.blueprints.v1.external_api import api


alerts_wrapper = {
	'query_name': fields.String(default = None),
	'message': fields.Raw(default = None),
	'node_id': fields.Integer(default = None),
	'rule_id': fields.Integer(default = None),
	'severity': fields.String(default = None),
	'created_at': fields.String(default = None),
	'type': fields.String(default = None),
	'source': fields.String(default = None),
	'source_data': fields.Raw(),
	'status': fields.String(default=None),
	'verdict':fields.String(default=None),
	'comment':fields.String(default=None),
	'updated_at':fields.String(default = None)
}


alert_analyst_notes_wrapper= {
	'id':fields.Integer(default=None),
	'notes': fields.Raw(default=None),
	'created_at': fields.DateTime(default=None),
	'updated_at': fields.DateTime(default=None),
	'user_id': fields.Integer(default=None)
}