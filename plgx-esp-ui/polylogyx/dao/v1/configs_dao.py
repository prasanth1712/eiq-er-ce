import datetime

from flask import abort
from flask import current_app
from sqlalchemy import or_, and_
from polylogyx.models import DefaultQuery, DefaultFilters, db, Config, Node, NodeConfig
from polylogyx.constants import DEFAULT_PLATFORMS

import datetime as dt


def add_config_by_platform(name, platform, conditions, description):
    return Config.create(name=name, platform=platform, conditions=conditions, description=description)


def add_default_query(name, sql, interval, status, config_id, snapshot=False, description=None, removed=True):
    return DefaultQuery.create(name=name, sql=sql, interval=interval, status=status, config_id=config_id, snapshot=snapshot, description=description, removed=removed)


def add_default_filters(filters, config):
    return DefaultFilters.create(filters=filters, config_id=config.id, created_at=dt.datetime.utcnow())


def add_queries_from_json(queries, config):
    default_config = db.session.query(Config).filter(Config.platform == config.platform).filter(
        Config.is_default).first()
    default_queries = db.session.query(DefaultQuery.name).filter(DefaultQuery.config_id == default_config.id).all()
    default_queries = [query[0] for query in default_queries]
    for query in queries:
        if query in default_queries:
            add_default_query(query, queries[query]['query'], queries[query]['interval'],
                queries[query]['status'], config.id,
                queries[query].get('snapshot', False),
                queries[query].get('description', None),
                queries[query].get('removed', True))


def get_all_configs():
    config_data = {}
    configs = Config.query.all()
    config_id_platform_dict = {config.id: config.platform for config in configs}
    default_queries = DefaultQuery.query.all()
    for query in default_queries:
        if query.config:
            name = query.config.name
            query_platform = config_id_platform_dict.get(query.config.id)
            if query_platform not in config_data:
                config_data[query_platform] = {}
            if name not in config_data[query_platform]:
                config_data[query_platform][name] = {"queries": {}}
            config_data[query_platform][name]["queries"][query.name] = query.to_dict()

    default_filters = DefaultFilters.query.all()

    for filter in default_filters:
        if filter.config:
            name = filter.config.name
            filter_platform = config_id_platform_dict.get(filter.config.id)
            if filter_platform not in config_data:
                config_data[filter_platform] = {}
            if name not in config_data[filter_platform]:
                config_data[filter_platform][name] = {"filters": {}}
            config_data[filter_platform][name]["filters"] = filter.filters
            config_data[filter_platform][name]['is_default'] = filter.config.is_default
            config_data[filter_platform][name]['id'] = filter.config.id
            config_data[filter_platform][name]["conditions"] = filter.config.conditions
            config_data[filter_platform][name]["description"] = filter.config.description

    return config_data


def get_config_dict(config):
    queries = {query.name: {'status': query.status, 'interval': query.interval} for query in
               DefaultQuery.query.filter(DefaultQuery.config_id == config.id).all()}
    filters = DefaultFilters.query.filter(DefaultFilters.config_id == config.id).first()
    if filters:
        filters = filters.filters
    else:
        filters = {}
    config_data = {"queries": queries, "filters": filters, "name": config.name, "description": config.description,
                   "conditions": config.conditions}
    return config_data


def delete_config(config):
    db.session.query(DefaultQuery).filter(DefaultQuery.config_id == config.id).delete(synchronize_session='fetch')
    db.session.query(DefaultFilters).filter(DefaultFilters.config_id == config.id).delete()
    return config.delete()


def assign_default_config_to_config_nodes(config):
    default_config = db.session.query(Config).filter(Config.platform == config.platform).filter(Config.is_default).first()
    node_config = db.session.query(NodeConfig).filter(NodeConfig.config_id == config.id).first()
    if node_config:
        db.session.query(NodeConfig).filter(NodeConfig.config_id == config.id).update({NodeConfig.config_id: default_config.id})
    db.session.commit()


def get_config(platform=None, config_id=None, name=None):
    if config_id:
        return db.session.query(Config).filter(Config.id == config_id).first()
    elif name and platform:
        return db.session.query(Config).filter(Config.name == name).filter(Config.platform == platform).first()
    elif platform:
        return db.session.query(Config).filter(Config.platform == platform).filter(
          Config.is_default).first()
    else:
        return


def edit_config_by_platform(config, filters, queries, name, conditions, description):
    # fetching the filters data to insert to the config dict
    dict_to_update = {}
    # Adding all the columns first into the dict_to_update dictionary and finally adding them to config with update method in one shot
    if description and not config.is_default:
        # No default config is allowed for description change from User Interface
        dict_to_update['description'] = description
    if name and not config.is_default:
        existing_config = get_config(platform=config.platform, name=name)
        if existing_config and not config.id == existing_config.id:
            # Config name per platform will be unique
            abort(400, 'Config with this name already exists!')
        dict_to_update['name'] = name
    if (conditions or conditions == {}) and not config.is_default:
        dict_to_update['conditions'] = conditions
    if dict_to_update:
        config.update(**dict_to_update)
    if filters:
        default_filters_obj = DefaultFilters.query.filter(DefaultFilters.config_id == config.id).first()
        if default_filters_obj:
            default_filters_obj.update(filters=filters)
    if queries:
        for key in list(queries.keys()):
            query = DefaultQuery.query.filter(DefaultQuery.name == key).filter(DefaultQuery.config_id == config.id).first()
            if query:
                # We just allow users to update status and interval but not anything else from UI, 
                # SQL and name are always allowed to choose from default configs only
                query.update(status=queries[key]['status'], interval=queries[key]['interval'])
    return True


def assign_node_config(config, nodes):
    for node in nodes:
        node_config = db.session.query(NodeConfig).filter(NodeConfig.node == node).first()
        if node_config:
            node_config.config = config
            node_config.update(node_config)
        else:
            node_config = NodeConfig(config_id=config.id, node_id=node.id)
            node_config.save()
    db.session.commit()
    return config


def is_configs_number_exceeded(platform):
    count = db.session.query(Config).filter(Config.platform == platform).count()
    if not count < current_app.config.get('POLYLOGYX_CUSTOM_CONFIG_LIMIT_PER_PLATFORM'):
        return True
    return False


def get_config_of_node(node):
    platform = node.platform
    if platform not in DEFAULT_PLATFORMS:
        platform = 'linux'
    node_config = db.session.query(NodeConfig).filter(NodeConfig.node == node).first()
    if node_config:
        return node_config.config
    else:
        return db.session.query(Config).filter(Config.platform == platform).filter(Config.is_default).first()


def get_nodes_list_of_config(config):
    if config.is_default:
        platform_filter = (Node.platform == config.platform)
        if config.platform == 'linux':
            platform_filter = Node.platform.notin_(('windows', 'darwin', 'freebsd'))
        node_ids = [item[0] for item in db.session.query(NodeConfig.node_id).all()]
        return db.session.query(Node).join(NodeConfig, 
                                                or_(and_(NodeConfig.config_id == config.id, NodeConfig.node_id == Node.id), 
                                                    and_(Node.id.notin_(node_ids), platform_filter))).all()
    else:
        return db.session.query(Node).join(NodeConfig, and_(NodeConfig.config_id == config.id, NodeConfig.node_id == Node.id)).all()


def is_config_conditions_json_valid(conditions):
    try:
        return (('hostname' in conditions and 'value' in conditions['hostname'] and conditions['hostname']['value']) or (
            'os_name' in conditions and 'value' in conditions['os_name'] and conditions['os_name']['value']))
    except:
        return False


def is_queries_dict_valid(queries):
    for query in queries:
        if 'status' not in queries[query] or 'interval' not in queries[query]:
            return False
    return True
