from flask_restplus import fields
from polylogyx.blueprints.v1.external_api import api


user_wrapper = api.model('users_wrapper', {
    'id': fields.Integer(),
    'username': fields.String(),
    'first_name': fields.String(),
    'last_name': fields.String()
})
