from flask_restplus import fields
from polylogyx.blueprints.v1.external_api import api

# Node Wrappers
node_info_wrapper = api.model('node_info_wrapper', {
    'computer_name': fields.String(),
    'hardware_model': fields.String(),
    'hardware_serial': fields.String(),
    'hardware_vendor': fields.String(),
    'physical_memory': fields.String(),
    'cpu_physical_cores': fields.String()
})

nodewrapper = api.model('nodewrapper', {
    'id':fields.Integer(),
    'host_identifier': fields.String(),
    'node_key': fields.String(),
    'last_ip': fields.String(),
    'platform': fields.String(),
    'os_info': fields.Raw(),
    'node_info': fields.Nested(node_info_wrapper, default=None),
    'network_info': fields.Raw(),
    'host_details': fields.Raw(),
    'last_checkin': fields.DateTime(default = None),
    'enrolled_on': fields.DateTime(default = None),
    'last_status': fields.DateTime(default = None),
    'last_result': fields.DateTime(default = None),
    'last_config': fields.DateTime(default = None),
    'last_query_read': fields.DateTime(default = None),
    'last_query_write': fields.DateTime(default = None),
})

node_tag_wrapper = api.model('node_tag_wrapper', {
    'host_identifier': fields.String(),
    'node_key': fields.String()
})

node_status_log_wrapper = api.model('node_status_log_wrapper', {
    'line': fields.Integer(),
    'message': fields.String(),
    'severity': fields.Integer(),
    'filename': fields.String(),
    'created': fields.DateTime(),
    'version': fields.String(),
})