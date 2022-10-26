from flask_restful import fields
from polylogyx.blueprints.v1.external_api import api

node_config =  {
    'status': fields.String(),
    'message': fields.String(),
    'data': fields.Raw(),
    'config': fields.Raw()
}
