from flask_restplus import fields
from polylogyx.blueprints.v1.external_api import api
from polylogyx.wrappers.v1 import user_wrappers

# Carves Wrapper

carves_wrapper = api.model('carves_wrapper', {
    'id': fields.Integer(),
    'node_id': fields.Integer(),
    'session_id': fields.String(),
    'carve_guid': fields.String(),
    'carve_size': fields.Integer(),
    'block_size': fields.Integer(),
    'block_count': fields.Integer(),
    'archive': fields.String(default=None),
    'status': fields.String(),
    'created_at': fields.DateTime()
})
