from flask_restful import Resource
from flask import abort
from polylogyx.blueprints.v1.external_api import api
from polylogyx.blueprints.v1.utils import *
from polylogyx.dao.v1 import configs_dao
from polylogyx.wrappers.v1 import parent_wrappers
from polylogyx.authorize import admin_required
from polylogyx.cache import refresh_cached_config



@api.resource('/configs/all', endpoint='list_configs')
class ConfigList(Resource):
    """
        Lists out all configs
    """
    def get(self):
        # Deprecated and is no longer supported
        current_app.logger.info("This api has been removed")
        abort(410, "This api has been removed, \
                   Please check the REST API documentation for more information about the new APIs")


@api.resource('/configs/view' ,endpoint='list_config_by_platform')
class GetConfigByPlatformOrNode(Resource):
    """
        Lists the config by its Platform or host_identifier
    """
    def post(self):
        # Deprecated and is no longer supported
        current_app.logger.info("This api has been removed")
        abort(410, "This api has been removed, \
                   Please check the REST API documentation for more information about the new APIs")


@api.resource('/configs/update', endpoint='update_config_by_platform')
class EditConfigByPlatform(Resource):
    """
        Lists or edits the config by its Platform
    """
    def post(self):
        # Deprecated and is no longer supported
        current_app.logger.info("This api has been removed")
        abort(410, "This api has been removed, \
                   Please check the REST API documentation for more information about the new APIs")


@api.resource('/configs/toggle' ,endpoint='toggle_config')
class ToggleConfigByPlatform(Resource):
    """
        Toggle default config between shallow and deep
    """
    def put(self):
        # Deprecated and is no longer supported
        current_app.logger.info("This api has been removed")
        abort(410, "This api has been removed, \
                   Please check the REST API documentation for more information about the new APIs")


@api.resource('/configs', endpoint='configs')
class Configs(Resource):
    """
        Configs Resource
    """
    post_parser = requestparse(['name', 'filters', 'queries', 'platform', 'conditions', 'description'],
                               [str, dict, dict, str, dict, str],
                               ["Name of the config", "json of filters", "json of queries",
                                "platform name(windows/linux/darwin)",
                                "conditions to auto assign config", "description of the config"],
                               [True, False, True, True, False, False],
                               [None, None, None, ["linux", "windows", "darwin"], None, None],
                               [None, {}, None, None, {}, None])
    get_parser = requestparse([], [], [], [], [])

    @admin_required
    def post(self):
        """
            Adds a new config by cloning other config or from list of queries and filters
        """
        args = self.post_parser.parse_args()
        name = args['name']
        args['name'] = args['name'].strip()  # Cropping out the spaces
        data = None
        status = "failure"
        if args['name'] is not None and not args['name']:
            message = 'Config name provided is not acceptable!'
        elif configs_dao.get_config(platform=args['platform'], name=args['name']):
            message = 'Config with this name already exists!'
        elif configs_dao.is_configs_number_exceeded(args['platform']):
            message = "Configs number limit of the platform is reached!"
        elif args['queries'] and not configs_dao.is_queries_dict_valid(args['queries']):
            message = "Please provide both interval and status for all queries!"
        elif not((args['conditions'] and configs_dao.is_config_conditions_json_valid(args['conditions']))
                 or (args['conditions'] == {})):
            message = "Conditions are not valid!"
        else:
            new_config = configs_dao.add_config_by_platform(args['name'], args['platform'], args['conditions'],
                                                    args['description'])
            configs_dao.add_queries_from_json(args['queries'], new_config)
            configs_dao.add_default_filters(args['filters'], new_config)
            refresh_cached_config()
            current_app.logger.info("Config is added for {0} platform with name - {1}".format(args['platform'], name))
            status = "success"
            message = "Config is added successfully"
            data = new_config.id
        return marshal(prepare_response(message, status, data), parent_wrappers.common_response_wrapper)


    def get(self):
        """
            Returns all configs present in db
        """
        data = configs_dao.get_all_configs()
        message = "Successfully fetched the config data"
        status = "success"
        if not data:
            data = {}
        return marshal(prepare_response(message, status, data), parent_wrappers.common_response_wrapper)


@api.resource('/configs/<int:config_id>' ,endpoint='config_by_id')
class Config(Resource):
    """
        Config by ID
    """
    get_parser = requestparse([], [], [], [], [])
    delete_parser = requestparse([], [], [], [], [])
    put_parser = requestparse(['filters', 'queries', 'name', 'conditions', 'description'], [dict, dict, str, dict, str],
                          ["filters to define for the specific platform", "queries to define for the specific platform",
                           "name of the config", "conditions to auto apply config on enroll", "description"],
                          [False, False, False, False, False], [None, None, None, None, None],
                          [None, None, None, None, None])

    
    def get(self, config_id=None):
        """
            Returns full dict config for the ID given
        """
        config = configs_dao.get_config(config_id=config_id)
        if config:
            data = configs_dao.get_config_dict(config)
            status = "success"
            message = "Fetched the config successfully"
            return marshal(prepare_response(message, status, data), parent_wrappers.common_response_wrapper)
        else:
            current_app.logger.info("Config id given is not a valid one!")
            abort(404, 'Config id is not valid!')

    @admin_required
    def put(self, config_id=None):
        """
            Modifies a config for ID given
        """
        args = self.put_parser.parse_args()
        config = configs_dao.get_config(config_id=config_id)
        queries = args['queries']
        filters = args['filters']
        conditions = args['conditions']
        description = args['description']
        if args['name']:
            args['name'] = args['name'].strip()  # Cropping out the spaces
        is_payload_valid = True
        message = None
        if config:
            if args['name'] is not None and not args['name']:
                message = "Config name provided is not acceptable!"
                is_payload_valid = False
            if queries:
                for query in queries:
                    if 'status' not in queries[query] or 'interval' not in queries[query]:
                        is_payload_valid = False
                        message = "Please provide both interval and status for all queries!"
                        current_app.logger.info("Interval and status are required for all queries!")
            if not((conditions and configs_dao.is_config_conditions_json_valid(conditions)) or (conditions == {})):
                message = "Conditions are not valid!"
                current_app.logger.info("Conditions are not proper!")
                is_payload_valid = False
            if is_payload_valid:
                configs_dao.edit_config_by_platform(config, filters, queries, args['name'], conditions, description)
                refresh_cached_config()
                current_app.logger.info(
                    "Config is updated for {0} platform with name {1}".format(config.platform, config.name))
                status = "success"
                message = "Config is updated successfully for the platform given"
            else:
                status = 'failure'
            return marshal(prepare_response(message, status), parent_wrappers.common_response_wrapper)
        else:
            current_app.logger.info('Config id is not valid!')
            abort(404, 'Config id is not valid!')

    @admin_required
    def delete(self, config_id=None):
        """
            Deletes a config with ID given
        """
        data = None
        config = configs_dao.get_config(config_id=config_id)
        if config and config.is_default:
            status = "failure"
            message = "Default configs cannot be deleted!"
            current_app.logger.info("Default configs cannot be deleted!")
            return marshal(prepare_response(message, status, data), parent_wrappers.common_response_wrapper)
        elif config:
            hosts = configs_dao.get_nodes_list_of_config(config)
            configs_dao.assign_default_config_to_config_nodes(config)
            data = configs_dao.delete_config(config)
            refresh_cached_config()
            status = "success"
            message = "Config is deleted successfully"
            current_app.logger.warning("Config is deleted successfully")
            return marshal(prepare_response(message, status, data), parent_wrappers.common_response_wrapper)
        else:
            current_app.logger.info("Config is not present for the id given!")
            abort(404, 'Config id is not valid!')


@api.resource('/configs/<int:config_id>/assign' ,endpoint='assign_config_by_id')
class AssignNodeConfig(Resource):
    """
        Assigns a config to single/multiple node(s)
    """
    parser = requestparse(['host_identifiers', 'tags'], [str, str], ["host identifiers", "tags"],
                          [False, False], [None, None], [None, None])

    @admin_required
    def put(self, config_id=None):
        """
            Assigns a config to single/multiple node(s)
        """
        args = self.parser.parse_args()
        config = configs_dao.get_config(config_id=config_id)
        if config:
            if args['host_identifiers'] or args['tags']:
                nodes = hosts_dao.get_nodes_list_by_host_ids(
                    [x.strip() for x in str(args['host_identifiers']).split(',')], [x.strip() for x in str(args['tags']).split(',')], config.platform)
                config = configs_dao.assign_node_config(config, nodes)
                current_app.logger.info(
                    "Config {0} is assigned for the hosts {1} and tags {2}".format(
                        config.name, args['host_identifiers'], args['tags']))
                status = "success"
                message = "Config is assigned to the hosts successfully"
                return marshal(prepare_response(message, status), parent_wrappers.common_response_wrapper)
            else:
                current_app.logger.info('Host Identifiers or Tags are required!')
                abort(400, 'Host Identifiers or Tags are required!')
        else:
            current_app.logger.info('Config id is not valid!')
            abort(404, 'Config id is not valid!')


@api.resource('/configs/<int:config_id>/hosts', endpoint='hosts_list_by_config')
class HostsListByConfig(Resource):
    """
        Hosts list by config id
    """
    parser = requestparse([], [], [], [], [], [])

    
    def get(self, config_id=None):
        """
            Hosts list by config id
        """
        config = configs_dao.get_config(config_id=config_id)
        if config:
            nodes = [node.get_dict() for node in configs_dao.get_nodes_list_of_config(config)]
            status = "success"
            message = "Hosts are retried for the config"
            return marshal(prepare_response(message, status, nodes), parent_wrappers.common_response_wrapper)
        else:
            current_app.logger.info('Config id is not valid!')
            abort(404, 'Config id is not valid!')
