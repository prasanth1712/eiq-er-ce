from flask_restplus import Namespace, Resource, marshal

from .utils import *
from polylogyx.dao import configs_dao as dao
from polylogyx.wrappers import parent_wrappers as parentwrapper

ns = Namespace('configs', description='Configurations resources blueprint')


@ns.route('', endpoint='list_configs')
class ConfigList(Resource):
    """Resource for Configs"""
    parser = requestparse([], [], [], [])

    @ns.doc(body=parser)
    @ns.expect(parser)
    def get(self):
        """Returns the default config used by PolyLogyx server agents"""
        data = dao.get_all_configs()
        message = "config is fetched successfully"
        status = "success"
        return marshal(prepare_response(message, status, data), parentwrapper.common_response_wrapper, skip_none=True)


@ns.route('/<any(windows,linux,darwin):platform>', endpoint='list_config_by_platform')
class ConfigByPlatform(Resource):
    """Resource for Configs View or Edit"""
    parser = requestparse(['filters', 'queries', 'arch', 'type'], [dict, dict, str, str],
                          ["filters to define for the specific platform", "queries to define for the specific platform", "arch of platform(x86/x86_64)", "type of the config(default/shallow/config)"], [True, True, False, False])

    @ns.doc(body=parser)
    @ns.expect(parser)
    def put(self, platform=None):
        """Updates config used by PolyLogyx agents"""
        args = self.parser.parse_args()
        arch = args['arch']
        if not arch:
           arch = "x86_64"
        type = args['type']
        if not type:
            type = "default"
        if platform == "windows" and arch == "x86_64" and type == "default":
            type = "shallow"
        type_mapping = {'default': 0, 'shallow': 1, 'deep': 2}
        config = dao.get_config_by_platform(platform, arch, type_mapping[type])
        config_dict = dao.edit_config_by_platform(config, args['filters'], args['queries'])
        status = "success"
        message = "Config is updated successfully"
        return marshal(prepare_response(message, status, config_dict), parentwrapper.common_response_wrapper, skip_none=True)
