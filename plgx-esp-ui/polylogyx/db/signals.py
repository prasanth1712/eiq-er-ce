import datetime as dt
from polylogyx.models import Rule, Alerts, Tag, Query, Pack, Config, Settings, DefaultFilters, \
    DefaultQuery, NodeConfig, ThreatIntelCredentials, VirusTotalAvEngines, IOCIntel, CarveSession, Node


table_map = {
        Rule: {'name': 'rule', 'column': 'rule_id', 'type': 'Rule'},
        Tag: {'name': 'tag', 'column': 'tag_id', 'type': 'Tag'},
        Query: {'name': 'query', 'column': 'query_id', 'type': 'Query'},
        Pack: {'name': 'pack', 'column': 'pack_id', 'type': 'Pack'},
        Config: {'name': 'config', 'column': 'config_id', 'type': 'Config'},
        Settings: {'name': 'settings', 'column': 'settings_id', 'type': 'Settings'},
        DefaultFilters: {'name': 'default_filters', 'column': 'default_filters_id', 'type': 'DefaultFilters'},
        DefaultQuery: {'name': 'default_query', 'column': 'default_query_id', 'type': 'DefaultQuery'},
        NodeConfig: {'name': 'node_config', 'column': 'node_config_id', 'type': 'NodeConfig'},
        ThreatIntelCredentials: {'name': 'threat_intel_credentials', 'column': 'threat_intel_credentials_id',
                                 'type': 'ThreatIntelCredentials'},
        VirusTotalAvEngines: {'name': 'virus_total_av_engines', 'column': 'virus_total_av_engines_id',
                              'type': 'VirusTotalAvEngines'},
        IOCIntel: {'name': 'ioc_intel', 'column': 'ioc_intel_id', 'type': 'IOCIntel'},
        CarveSession: {'name': 'carve_session', 'column': 'carve_session_id', 'type': 'CarveSession'},
        Alerts: {'name': 'alerts', 'column': 'alert_id', 'type': 'Alerts'},
        Node: {'name': 'node', 'column': 'node_id', 'type': 'Node'}
}


def receive_after_update(mapper, connection, target):
    """
    listen for the 'after_update' event
    """
    from polylogyx.dao.v1.users_dao import get_current_user
    current_user = get_current_user()
    if current_user:
        table_name = table_map.get(type(target), {}).get('name')
        if hasattr(target, 'updated_at') and table_name:
            connection.execute(
                "update {0} set updated_at='{1}' where id={2};"
                .format(table_name, str(dt.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')), target.id))
        create_platform_activity_obj(connection, 'updated', target, current_user.id)


def receive_after_insert(mapper, connection, target):
    """
    listen for the 'after_insert' event
    """
    from polylogyx.dao.v1.users_dao import get_current_user
    current_user = get_current_user()
    if current_user:
        create_platform_activity_obj(connection, 'created', target, current_user.id)


def receive_after_delete(mapper, connection, target):
    """
    listen for the 'after_delete' event
    """
    from polylogyx.dao.v1.users_dao import get_current_user
    current_user = get_current_user()
    if current_user:
        text = "{0} with id '{1}' has been deleted".format(table_map.get(type(target), {}).get('type'), target.id)
        connection.execute(
            "insert into platform_activity (action, user_id, text, created_at) values ('{0}', {1}, $${2}$$, '{3}')".format(
                'deleted', current_user.id, text, str(dt.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f'))))


def create_platform_activity_obj(connection, action, target, user_id):
    column_name = table_map.get(type(target), {}).get('column')
    if column_name and action != 'deleted' and action != 'delete':
        connection.execute("""
            insert into platform_activity (action, user_id, {0}, created_at) values ('{1}', {2}, {3}, '{4}')""".format(
            column_name, action, user_id, target.id, str(dt.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f'))))
