from flask_restplus import fields
from polylogyx.blueprints.v1.external_api import api


alerts_wrapper = api.model('alerts_wrapper', {
	'query_name': fields.String(default = None),
	'message': fields.Raw(default = None),
	'node_id': fields.Integer(default = None),
	'rule_id': fields.Integer(default = None),
	'severity': fields.String(default = None),
	'created_at': fields.String(default = None),
	'type': fields.String(default = None),
	'source': fields.String(default = None),
	'recon_queries': fields.Raw(default=None),
	'status': fields.String(default=None),
	'source_data': fields.Raw()
})


alert_analyst_notes_wrapper= api.model('alert_analyst_notes_wrapper',{
	'id':fields.Integer(default=None),
	'notes': fields.Raw(default=None),
	'created_at': fields.DateTime(default=None),
	'updated_at': fields.DateTime(default=None),
	'user_id': fields.Integer(default=None)
})