from flask_restful import fields
from polylogyx.blueprints.v1.external_api import api
# ResultLog Wrapper

result_log_wrapper = {
    'id': fields.Integer(),
    'name': fields.String(),
    'timestamp': fields.DateTime(),
    'action': fields.String(),
    'columns': fields.Raw(default = None),
    'node_id': fields.Integer()
}
