import json
import copy
import datetime
import statistics
import requests
from requests.auth import HTTPBasicAuth
import collections.abc

from flask import current_app

from polylogyx.db.models import Rule, Node, Settings, Config, DefaultFilters, DefaultQuery, db, IOCIntel
from polylogyx.constants import IOC_COLUMNS, CacheVariables
from polylogyx.extensions import redis_client
from polylogyx.utils.config import assemble_options


def get_average_celery_task_wait_time():
    data = redis_client.get(CacheVariables.avg_task_wait_time)
    if data:
        return data
    else:
        try:
            response = requests.get(
                """{}/api/tasks?limit=5&&sort_by=started&&
            taskname=polylogyx.celery.tasks.save_and_analyze_results&&state=SUCCESS""".format(
                    current_app.config["FLOWER_URL"]
                ),
                params="",
                auth=HTTPBasicAuth(current_app.config["FLOWER_USERNAME"], current_app.config["FLOWER_PASSWORD"]),
                timeout=30,
            )
            task_wait_time_list = []
            for key, value in response.json().items():
                task_wait_time_list.append(value["succeeded"] - value["received"])
            data = statistics.mean(task_wait_time_list)
            redis_client.set(CacheVariables.avg_task_wait_time, data)
        except Exception as e:
            print("""Unable to cache the celery task stats of result log processing task, {}""".format(str(e)))


def merge_dicts(base_dict, dict_to_merge):
    for key, value in dict_to_merge.items():
        if isinstance(value, collections.abc.Mapping):
            base_dict[key] = merge_dicts(base_dict.get(key, {}), value)
        elif isinstance(value, datetime.datetime):
            base_dict[key] = str(value)
        elif base_dict.get(key) and not value:
            pass
        else:
            base_dict[key] = value
    return base_dict


def get_host_dict(node):
    """
    Returns a dictionary formatted host by accepting Node obj
    """
    node_dict = {
        'id': node.id,
        'host_identifier': node.host_identifier,
        'hostname': node.display_name,
        'node_key': node.node_key,
        'state': node.state,
        'platform': node.platform,
        'last_ip': node.last_ip,
        'host_details': node.host_details
    }
    for column in ['enrolled_on', 'last_checkin', 'last_status', 'last_result', 'last_config', 'last_query_read', 'last_query_write']:
        if getattr(node, column):
            node_dict[column] = str(getattr(node, column))
        else:
            node_dict[column] = getattr(node, column)
    return node_dict
    

def get_rule_dict(rule):
    """
    Returns a dictionary formatted rule by accepting Rule obj
    """
    return {
        'id': rule.id,
        'name': rule.name,
        'platform': rule.platform,
        'conditions': rule.conditions,
        'severity': rule.severity,
        'status': rule.status,
        'description': rule.description,
        'alerters': rule.alerters,
        'alert_description': rule.alert_description
    }


# Config's section
def fetch_all_configs():
    """
    Queries all configs from database and returns them in dict format
    """
    configs_dict = {}
    configs = db.session.query(Config).all()
    for config in configs:
        if config.platform not in configs_dict:
            configs_dict[config.platform] = {}
        # assemble filters
        config_filter = DefaultFilters.query.filter(DefaultFilters.config == config).first()
        if config_filter and config_filter.filters:
            configs_dict[config.platform][config.name] = config_filter.filters
        else:
            configs_dict[config.platform][config.name] = {}

        # assemble schedule
        schedule = {}
        queries = db.session.query(DefaultQuery).filter(DefaultQuery.config == config).filter(DefaultQuery.status).all()
        version_queries = (
            db.session.query(DefaultQuery).filter(DefaultQuery.config == None).filter(DefaultQuery.status).all()
        )
        for default_query in queries:
            schedule[default_query.name] = default_query.to_dict()
        for default_query in version_queries:
            schedule[default_query.name] = default_query.to_dict()
        configs_dict[config.platform][config.name]["schedule"] = schedule
        configs_dict[config.platform][config.name]["options"] = assemble_options(
            configs_dict[config.platform][config.name]
        )
    return configs_dict


def get_all_configs():
    """
    Fetches configs from cache if present else fetches from db, Returns in dict format
    """
    cached_data = redis_client.get(CacheVariables.configs)
    if cached_data:
        data = json.loads(cached_data.decode("utf-8"))
    else:
        data = fetch_all_configs()
        redis_client.set(CacheVariables.configs, json.dumps(data))
    return data


def refresh_cached_config():
    """
    Refreshes the configs cached by fetching configs from db, Returns in dict format
    """
    data = fetch_all_configs()
    redis_client.set(CacheVariables.configs, json.dumps(data))
    return data


# Hosts section
def fetch_all_hosts():
    """
    Caching all the hosts with their frequently used attributes,
    Using node_key and host_identifier pair allows accessing nodes easily and fast in esp container
    All these will be mostly used in esp container node_required decorator and all other places than querying everytime
    """
    nodes_dict = {}
    nodes = Node.query.filter(Node.state.in_((Node.REMOVED, Node.ACTIVE))).all()
    for node in nodes:
        nodes_dict[node.node_key] = get_host_dict(node)
    return nodes_dict


def get_all_cached_hosts():
    """
    Returns cached hosts if present else fetches from db and returns
    """
    cached_data = redis_client.hgetall(CacheVariables.hosts)
    if cached_data:
        dict_to_return = {}
        for key, value in cached_data.items():
            dict_to_return[key.decode('utf-8')] = json.loads(value.decode('utf-8'))
    else:
        dict_to_return = fetch_all_hosts()
        data = copy.deepcopy(dict_to_return)
        for key, value in data.items():
            data[key] = json.dumps(value)
        if data:
            redis_client.hmset(CacheVariables.hosts, data)
    return dict_to_return


def refresh_cached_hosts():
    """
    Deletes all the cached hosts and updates them with the values fetched from db
    """
    data = fetch_all_hosts()
    if data:
        cached_hosts = redis_client.hgetall(CacheVariables.hosts)
        cached_hosts_dict = {}
        for key, value in cached_hosts.items():
            cached_hosts_dict[key.decode('utf-8')] = json.loads(value.decode('utf-8'))
        host_keys = list(cached_hosts_dict.keys())
        data = merge_dicts(data, cached_hosts_dict)
        for key, value in data.items():
            data[key] = json.dumps(value)
        if host_keys:
            redis_client.hdel(CacheVariables.hosts, *host_keys)
        redis_client.hmset(CacheVariables.hosts, data)
    else:
        redis_client.delete(CacheVariables.hosts)


def add_or_update_cached_host(node_id=None, node_key=None, host_identifier=None, node_obj=None):
    """
    Refreshes a cached host
    """
    node_info = {}
    if node_id:
        node_obj = Node.query.filter(Node.id == node_id).first()
        node_info = {'id': node_id}
    elif host_identifier:
        node_obj = Node.query.filter(Node.host_identifier == host_identifier).first()
        node_info = {'host_identifier': host_identifier}
    elif node_key:
        node_obj = Node.query.filter(Node.node_key == node_key).first()
        node_info = {'node_key': node_key}
    if isinstance(node_obj, Node):
        redis_client.hdel(CacheVariables.hosts, node_obj.node_key)
        redis_client.hmset(CacheVariables.hosts, {node_obj.node_key: json.dumps(get_host_dict(node_obj))})
    elif node_info:
        for column_name, column_value in node_info.items():
            current_app.logger.error(f"Could not refresh the cached host with {column_name} '{column_value}'!")
            break


def remove_cached_host(node_id=None, node_key=None, host_identifier=None):
    """
    Removes a host entry from redis cache
    """
    if node_id or host_identifier:
        hosts = get_all_cached_hosts()
        for node_key_cached, host_dict in hosts.items():
            if (node_id and host_dict['id'] == node_id) or (host_identifier and host_dict['host_identifier'] == host_identifier):
                node_key = node_key_cached
                break
    if node_key:
        redis_client.hdel(CacheVariables.hosts, node_key)


def update_cached_host(node_key, data):
    """
    Updates a cached host columns in redis cache
    """
    host = redis_client.hmget(CacheVariables.hosts, node_key)
    if not host or not host[0]:
        add_or_update_cached_host(node_key=node_key)
        host = redis_client.hmget(CacheVariables.hosts, node_key)
    host = json.loads(host[0].decode('utf-8'))
    host = merge_dicts(host, data)
    redis_client.hmset(CacheVariables.hosts, {node_key: json.dumps(host)})


def get_a_host(node_key=None, host_identifier=None):
    """
    Returns a host dict if present in cache else fetches from db
    """
    host = None
    if node_key:
        cached_host = redis_client.hmget(CacheVariables.hosts, node_key)
        if cached_host and cached_host[0]:
            host = json.loads(cached_host[0].decode('utf-8'))
    elif host_identifier:
        all_hosts = get_all_cached_hosts()
        for node_key, host_dict in all_hosts.items():
            if host_dict['host_identifier'] == host_identifier:
                host = host_dict
                break
    if not host:
        node_obj = None
        if node_key:
            node_obj = Node.query.filter(Node.node_key == node_key).first()
        elif host_identifier:
            node_obj = Node.query.filter(Node.host_identifier == host_identifier).first()
        if node_obj:
            host = get_host_dict(node_obj)
    return host


# Rules section
def fetch_all_rules():
    """
    Caching all rules helps in querying them better and scalable in rule matching engine.
    Caching only ACTIVE rules because no where we are trying to access inactive rules
    As rules will be queries by platform, platform is being used as key
    """
    rules_dict = {}
    rules = Rule.query.filter(Rule.status == Rule.ACTIVE).all()
    for rule in rules:
        rules_dict[rule.name] = get_rule_dict(rule)
    return rules_dict


def get_all_cached_rules():
    """
    Returns all cached rules if present else fetches from db and returns
    """
    cached_data = redis_client.hgetall(CacheVariables.rules)
    if cached_data:
        dict_to_return = {}
        for key, value in cached_data.items():
            dict_to_return[key.decode('utf-8')] = json.loads(value.decode('utf-8'))
    else:
        dict_to_return = fetch_all_rules()
        data = copy.deepcopy(dict_to_return)
        for key, value in data.items():
            data[key] = json.dumps(value)
        if data:
            redis_client.hmset(CacheVariables.rules, data)
    return dict_to_return


def refresh_cached_rules():
    """
    Refreshes all cached rules with the values present in db
    """
    data = fetch_all_rules()
    for key, value in data.items():
        data[key] = json.dumps(value)
    if data:
        rule_keys = redis_client.hgetall(CacheVariables.rules)
        rule_keys = [key.decode('utf-8') for key in rule_keys.keys()]
        if rule_keys:
            redis_client.hdel(CacheVariables.rules, *rule_keys)
        redis_client.hmset(CacheVariables.rules, data)
        redis_client.delete(CacheVariables.rule_network)
    else:
        redis_client.delete(CacheVariables.rules)


def add_or_update_cached_rule(rule_id=None, rule_name=None, rule_obj=None):
    """
    Adds or updates the rule in to redis
    """
    rule_info = {}
    if rule_name:
        rule_obj = Rule.query.filter(Rule.name == rule_name).first()
        rule_info = {'name': rule_name}
    elif rule_id:
        rule_obj = Rule.query.filter(Rule.id == rule_id).first()
        rule_info = {'id': rule_id}
    if isinstance(rule_obj, Rule):
        if rule_obj.status == Rule.ACTIVE:
            # Rule will be cached only when its state is ACTIVE for performance improvements
            redis_client.hdel(CacheVariables.rules, rule_obj.name)
            redis_client.hmset(CacheVariables.rules, {rule_obj.name: json.dumps(get_rule_dict(rule_obj))})
        elif rule_obj:
            # In rule update to INACTIVE case this will be triggered and will be removed from cache
            redis_client.hdel(CacheVariables.rules, rule_obj.name)
        else:
            for column_name, column_value in rule_info.items():
                current_app.logger.error(f"Rule cannot be found for the {column_name} -- '{column_value}'!")
                break
    elif rule_info:
        for column_name, column_value in rule_info.items():
            current_app.logger.error(f"Could not refresh the cached rule with {column_name} '{column_value}'!")
            break


def remove_cached_rule(rule_id=None, rule_name=None):
    """
    Remove a rule entry from redis location
    """
    if rule_id:
        rules = get_all_cached_rules()
        for name, rule_dict in rules.items():
            if rule_dict['id'] == rule_id:
                rule_name = name
                break
    if rule_name:
        redis_client.hdel(CacheVariables.rules, rule_name)


def get_a_rule(rule_name=None, rule_id=None):
    """
    Get a rule from redis if present else from db
    """
    rule = None
    if rule_name:
        cached_rule = redis_client.hmget(CacheVariables.rules, rule_name)
        if cached_rule and cached_rule[0]:
            rule = json.loads(cached_rule[0].decode('utf-8'))
    elif rule_id:
        all_rules = get_all_cached_rules()
        for name, rule_dict in all_rules.items():
            if rule_id == rule_dict['id']:
                rule = rule_dict
                break
    if not rule:
        rule_obj = None
        if rule_name:
            rule_obj = Rule.query.filter(Rule.name == rule_name).first()
        elif rule_id:
            rule_obj = Rule.query.filter(Rule.id == rule_id).first()
        if rule_obj:
            rule =  get_rule_dict(rule_obj)
    return rule


# Settings section
def fetch_all_settings():
    """
    Caching all settings irrespective of their data type or the place being used.
    So that all settings like alert aggregation time, log level, VT retention days etc., will be accessed without querying them from db
    """
    settings_dict = {}
    all_settings = Settings.query.all()
    for setting_obj in all_settings:
        settings_dict[setting_obj.name] = setting_obj.setting
    return settings_dict


def get_all_cached_settings():
    """
    Returns all the cached settings if present else returns the values present in db
    """
    cached_data = redis_client.hgetall(CacheVariables.settings)
    if cached_data:
        dict_to_return = {}
        for key, value in cached_data.items():
            dict_to_return[key.decode('utf-8')] = value.decode('utf-8')
        data = dict_to_return
    else:
        data = fetch_all_settings()
        if data:
            redis_client.hmset(CacheVariables.settings, data)
    return data


def refresh_cached_settings():
    """
    Refresh all the settings present in redis with the values in db
    """
    data = fetch_all_settings()
    if data:
        settings_keys = redis_client.hgetall(CacheVariables.settings)
        settings_keys = [key.decode('utf-8') for key in settings_keys.keys()]
        if settings_keys:
            redis_client.hdel(CacheVariables.settings, *settings_keys)
        redis_client.hmset(CacheVariables.settings, data)
    else:
        redis_client.delete(CacheVariables.settings)


def update_cached_setting(name, value):
    """
    Updates a setting value present in redis cache
    """
    if value:
        redis_client.hmset(CacheVariables.settings, {name: value})


def add_or_update_cached_setting(setting_id=None, setting_name=None, setting_obj=None):
    """
    Adds or updates the setting in to redis
    """
    setting_info = {}
    if setting_name:
        setting_obj = Settings.query.filter(Settings.name == setting_name).first()
        setting_info = {'name': setting_name}
    elif setting_id:
        setting_obj = Settings.query.filter(Settings.id == setting_id).first()
        setting_info = {'id': setting_id}
    if isinstance(setting_obj, Settings):
        setting_info = {'name': setting_obj.name}
        redis_client.hdel(CacheVariables.settings, setting_obj.name)
        redis_client.hmset(CacheVariables.settings, {setting_obj.name: setting_obj.setting})
    elif setting_info:
        for column_name, column_value in setting_info.items():
            current_app.logger.error(f"Could not refresh the cached setting with {column_name} '{column_value}'!")
            break


def remove_cached_setting(setting_name=None):
    """
    Remove a setting entry from redis location
    """
    if setting_name:
        redis_client.hdel(CacheVariables.settings, setting_name)


def get_a_setting(name):
    """
    Returns a cached setting if present else returns from db
    """
    setting = None
    cached_setting = redis_client.hmget(CacheVariables.settings, name)
    if cached_setting and cached_setting[0]:
        setting = cached_setting[0].decode("utf-8") 
    else:
        setting_obj = Settings.query.filter(Settings.name == name).first()
        if setting_obj:
            setting = setting_obj.setting
    return setting


# Node alerts count section
def get_rule_node_latest_alerts(node_id):
    all_node_alerts = redis_client.hmget(CacheVariables.node_rule_alerts, node_id)
    if all_node_alerts and all_node_alerts[0]:
        all_node_alerts = json.loads(all_node_alerts[0].decode('utf-8'))
        for rule_id, alert_id_dict in all_node_alerts.items():
            if isinstance(alert_id_dict['created_at'], str):
                alert_id_dict['created_at'] = datetime.datetime.strptime(alert_id_dict['created_at'], "%Y-%m-%d %H:%M:%S.%f")
    else:
        all_node_alerts = {}
    return all_node_alerts


def update_rule_node_latest_alert(node_id, rule_alert_id_dict):
    all_alerts = redis_client.hmget(CacheVariables.node_rule_alerts, node_id)
    if all_alerts and all_alerts[0]:
        all_alerts = json.loads(all_alerts[0].decode('utf-8'))
    else:
        all_alerts = {}
    for rule_id, alert_id_dict in rule_alert_id_dict.items():
        alert_id_dict['created_at'] = str(alert_id_dict['created_at'])  # Time stamps cannot be converted into JSON
        all_alerts[rule_id] = alert_id_dict
    redis_client.hmset(CacheVariables.node_rule_alerts, {node_id: json.dumps(all_alerts)})
    return True


# IOCs section
def load_db_iocs():
    """
    Fetches all the IOCs from db and serializes them
    """
    iocs = IOCIntel.query.with_entities(IOCIntel.type, IOCIntel.value, IOCIntel.severity).all()
    intels = {}
    for ioc in iocs:
        if ioc.type in intels.keys():
            intels[ioc.type][ioc.value] = ioc.severity
        else:
            if ioc.type in set(IOC_COLUMNS):
                intels[ioc.type] = {ioc.value: ioc.severity}
    return intels


def load_cached_iocs():
    """
    Returns all the cached IOCs if present else fetches from db and returns
    """
    cached_data = redis_client.hgetall(CacheVariables.iocs)
    if cached_data:
        dict_to_return = {}
        for key, value in cached_data.items():
            dict_to_return[key.decode('utf-8')] = json.loads(value.decode('utf-8'))
        data = dict_to_return
    else:
        data = load_db_iocs()
        for type, value_severity in data.items():
            data[type] = json.dumps(value_severity)
        if data:
            redis_client.hmset(CacheVariables.iocs, data)
    return data


def refresh_cached_iocs():
    """
    Refreshes the cached iocs with the values in db
    """
    intels = load_db_iocs()
    for type, value_severity in intels.items():
        intels[type] = json.dumps(value_severity)
    if intels:
        ioc_keys = redis_client.hgetall(CacheVariables.iocs)
        ioc_keys = [key.decode('utf-8') for key in ioc_keys.keys()]
        if ioc_keys:
            redis_client.hdel(CacheVariables.iocs, *ioc_keys)
        redis_client.hmset(CacheVariables.iocs, intels)
    else:
        redis_client.delete(CacheVariables.iocs)
