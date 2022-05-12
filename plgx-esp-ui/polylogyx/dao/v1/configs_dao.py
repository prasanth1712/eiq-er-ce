import datetime

from flask import abort
from flask import current_app
from sqlalchemy import or_, and_
from polylogyx.models import DefaultQuery, DefaultFilters, db, Config, Node, NodeConfig
from polylogyx.constants import DEFAULT_PLATFORMS

import datetime as dt


def add_config_by_platform(name, platform, conditions, description):
    return Config.create(name=name, platform=platform, conditions=conditions, description=description)


def add_default_query(name, platform, sql, interval, status, config_id, snapshot=False, description=None, removed=True):
    return DefaultQuery.create(name=name, platform=platform, sql=sql, interval=interval, status=status, config_id=config_id, snapshot=snapshot, description=description, removed=removed)


def add_default_filters(filters, platform, config):
    return DefaultFilters.create(filters=filters, platform=platform, config_id=config.id, created_at=dt.datetime.utcnow())


def add_queries_from_json(queries, platform, config):
    default_config = db.session.query(Config).filter(Config.platform == config.platform).filter(
        Config.is_default).first()
    default_queries = db.session.query(DefaultQuery.name).filter(DefaultQuery.config_id == default_config.id).all()
    default_queries = [query[0] for query in default_queries]
    for query in queries:
        if query in default_queries:
            add_default_query(query, platform, queries[query]['query'], queries[query]['interval'],
                queries[query]['status'], config.id,
                queries[query].get('snapshot', False),
                queries[query].get('description', None),
                queries[query].get('removed', True))


def get_all_configs():
    config_data = {}
    default_queries = DefaultQuery.query.all()

    for query in default_queries:
        if query.config:
            name = query.config.name
            if not query.platform in config_data:
                config_data[query.platform] = {}
            if not name in config_data[query.platform]:
                config_data[query.platform][name] = {"queries": {}}
            config_data[query.platform][name]["queries"][query.name] = query.to_dict()

    default_filters = DefaultFilters.query.all()

    for filter in default_filters:
        if filter.config:
            name = filter.config.name
            if not filter.platform in config_data:
                config_data[filter.platform] = {}
            if not name in config_data[filter.platform]:
                config_data[filter.platform][name] = {"filters": {}}
            config_data[filter.platform][name]["filters"] = filter.filters
            config_data[filter.platform][name]['is_default'] = filter.config.is_default
            config_data[filter.platform][name]['id'] = filter.config.id
            config_data[filter.platform][name]["conditions"] = filter.config.conditions
            config_data[filter.platform][name]["description"] = filter.config.description

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
    if description and not config.is_default:
        config.update(description=description)
    if name and not config.is_default:
        existing_config = get_config(platform=config.platform, name=name)
        if existing_config and not config.id == existing_config.id:
            abort(400, 'Config with this name already exists!')
        config.update(name=name)
    if (conditions or conditions == {}) and not config.is_default:
        config.update(conditions=conditions)
    if filters:
        default_filters_obj = DefaultFilters.query.filter(DefaultFilters.config_id == config.id).first()
        if default_filters_obj:
            default_filters_obj.update(filters=filters)
    if queries:
        for key in list(queries.keys()):
            query = DefaultQuery.query.filter(DefaultQuery.name == key).filter(DefaultQuery.config_id == config.id).first()
            if query:
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
    platform_filter = Node.platform == config.platform
    if config.platform == 'linux':
        platform_filter = ~Node.platform.in_(('windows', 'darwin', 'freebsd'))
    return db.session.query(Node).outerjoin(NodeConfig)\
        .filter(or_(NodeConfig.config_id == config.id,
                    and_(~Node.id.in_(db.session.query(NodeConfig.node_id).all()), config.is_default)))\
        .filter(platform_filter).all()


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
