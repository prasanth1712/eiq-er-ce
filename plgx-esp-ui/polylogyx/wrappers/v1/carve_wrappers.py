from flask_restful import fields


# Carves Wrapper

carves_wrapper = {
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
}
