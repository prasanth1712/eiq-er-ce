#from flask_restful import fields
#from polylogyx.blueprints.v1.external_api import api

from flask_restful import fields

response_parent =  {
    'status': fields.String(default='success'),
}

failure_response_parent = {
    'status': fields.String(default='failure'),
    'message': fields.String(default='some error has occured')
}


common_response_wrapper = {
    'status': fields.String,
    'message': fields.String,
    'data': fields.Raw
}


common_response_with_errors_wrapper =  {
    'status': fields.String(),
    'message': fields.String(),
    'data': fields.Raw(),
    'errors': fields.Raw(),
}
