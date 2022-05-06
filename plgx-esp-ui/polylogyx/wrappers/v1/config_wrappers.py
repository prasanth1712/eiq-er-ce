from flask_restplus import fields
from polylogyx.blueprints.v1.external_api import api

node_config = api.model('node_full_config_wrapper', {
    'status': fields.String(description=u'status'),
    'message': fields.String(description=u'message about the status'),
    'data': fields.Raw(description=u'data if present'),
    'config': fields.Raw(description=u'config id and name')
})
