from flask_restplus import fields
from polylogyx.blueprints.v1.external_api import api


response_parent = api.model('response', {
    'status': fields.String(default='success'),
})

failure_response_parent = api.model('failure_response_wrapper', {
    'status': fields.String(default='failure'),
    'message': fields.String(default='some error has occured')
})

common_response_wrapper = api.model('common_response_wrapper', {
    'status': fields.String(description=u'status'),
    'message': fields.String(description=u'message about the status'),
    'data': fields.Raw(description=u'data if present')
})


common_response_with_errors_wrapper = api.model('common_response_with_errors_wrapper', {
    'status': fields.String(description=u'status'),
    'message': fields.String(description=u'message about the status'),
    'data': fields.Raw(description=u'data if present'),
    'errors': fields.Raw(description=u'errors if present'),
})
