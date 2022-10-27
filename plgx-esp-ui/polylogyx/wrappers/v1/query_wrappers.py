from flask_restful import fields
from .parent_wrappers import response_parent
from polylogyx.blueprints.v1.external_api import api

query_wrapper = {
    'id':fields.Integer(),
    'name' : fields.String(),
    'sql' : fields.String(default = None),
    'interval' : fields.Integer(default = None),
    'platform' : fields.String(default = None),
    'version' : fields.String(default = None),
    'description' : fields.String(default = None),
    'value' : fields.String(default = None),
    'snapshot' : fields.Boolean(default = None),
    'shard' : fields.Integer(default = None),
}

add_query_wrapper = {
    'status': fields.String(default='success'),
    'query_id': fields.Integer(),
    'message': fields.String(default = "Successfully added the query for the data given")
}