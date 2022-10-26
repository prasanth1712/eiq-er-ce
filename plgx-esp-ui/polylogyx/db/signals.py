import datetime as dt
import inspect


def receive_after_update(mapper, connection, target):
    """
    listen for the 'after_update' event
    """
    from polylogyx.dao.v1.users_dao import get_current_user
    current_user = get_current_user()
    if current_user:
        if hasattr(target, 'updated_at') and target.__tablename__:
            connection.execute(
                """update "{0}" set updated_at='{1}' where id={2};"""
                .format(target.__tablename__, str(dt.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')), target.id))
        create_platform_activity_obj(connection, 'updated', target, current_user.id)

    # This will be made dynamic in next sprint
    from polylogyx.models import Node, Rule, Settings
    from polylogyx.cache import add_or_update_cached_host, add_or_update_cached_rule, add_or_update_cached_setting
    if type(target) is Node:
        add_or_update_cached_host(node_obj=target)
    if type(target) is Rule:
        add_or_update_cached_rule(rule_obj=target)
    if type(target) is Settings:
        add_or_update_cached_setting(setting_obj=target)


def receive_after_insert(mapper, connection, target):
    """
    listen for the 'after_insert' event
    """
    from polylogyx.dao.v1.users_dao import get_current_user
    current_user = get_current_user()
    if current_user:
        create_platform_activity_obj(connection, 'created', target, current_user.id)

    # This will be made dynamic in next sprint
    from polylogyx.models import Node, Rule, Settings
    from polylogyx.cache import add_or_update_cached_host, add_or_update_cached_rule, add_or_update_cached_setting
    if type(target) is Node:
        add_or_update_cached_host(node_obj=target)
    if type(target) is Rule:
        add_or_update_cached_rule(rule_obj=target)
    if type(target) is Settings:
        add_or_update_cached_setting(setting_obj=target)


def receive_after_delete(mapper, connection, target):
    """
    listen for the 'after_delete' event
    """
    from polylogyx.dao.v1.users_dao import get_current_user
    current_user = get_current_user()
    if current_user:
        text = "{0} with id '{1}' has been deleted".format(target.__class__.__name__, target.id)
        connection.execute(
            "insert into platform_activity (action, user_id, text, created_at, entity, entity_id) values ('{0}', {1}, $${2}$$, '{3}', '{4}', {5})".format(
                'deleted', current_user.id, text, str(dt.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')), target.__tablename__, target.id))

    # This will be made dynamic in next sprint
    from polylogyx.models import Node, Rule, Settings
    from polylogyx.cache import remove_cached_host, remove_cached_rule, remove_cached_setting
    if type(target) is Node:
        remove_cached_host(node_id=target.id)
    if type(target) is Rule:
        remove_cached_rule(rule_id=target.id)
    if type(target) is Settings:
        remove_cached_setting(setting_name=target.name)


def receive_after_bulk_delete(delete_context):
    """
    listen for the 'after_bulk_delete' event
    """
    from polylogyx.cache import refresh_cached_rules, refresh_cached_hosts, refresh_cached_config, refresh_cached_settings, refresh_cached_iocs
    class_name = None
    column_descriptions = delete_context.query.column_descriptions
    if column_descriptions:
        class_name = column_descriptions[0]['name']
        if class_name == 'Rule':
            refresh_cached_rules()
        elif class_name == 'Config':
            refresh_cached_config()
        elif class_name == 'Node':
            refresh_cached_hosts()
        elif class_name == 'Settings':
            refresh_cached_settings()
        elif class_name == 'IOCIntel':
            refresh_cached_iocs()


def receive_after_bulk_update(update_context):
    """
    listen for the 'after_bulk_update' event
    """
    from polylogyx.cache import refresh_cached_rules, refresh_cached_hosts, refresh_cached_config, refresh_cached_settings, refresh_cached_iocs
    class_name = None
    column_descriptions = update_context.query.column_descriptions
    if column_descriptions:
        class_name = column_descriptions[0]['name']
        if class_name == 'Rule':
            refresh_cached_rules()
        elif class_name == 'Config':
            refresh_cached_config()
        elif class_name == 'Node':
            refresh_cached_hosts()
        elif class_name == 'Settings':
            refresh_cached_settings()
        elif class_name == 'IOCIntel':
            refresh_cached_iocs()


def create_platform_activity_obj(connection, action, target, user_id):
    """
    Inserts a row to platform_activity table
    """
    import inspect
    if not target:
        target_id = None
        target_table = None
    elif inspect.isclass(target):
        target_id = None
        target_table = target.__tablename__
    else:
        target_id = target.id
        target_table = target.__tablename__
    if not target_id:
        target_id = 'null'
    if action != 'deleted' and action != 'delete':
        connection.execute("""
            insert into platform_activity (action, user_id, entity, entity_id, created_at) values ('{0}', {1}, '{2}', {3}, '{4}')""".format(
            action, user_id, target_table, target_id, str(dt.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f'))))


def bulk_insert_to_pa(connection, action, target, entity_ids):
    """
    Inserts multiple rows to platform_activity table
    """
    from polylogyx.dao.v1.users_dao import get_current_user
    current_user = get_current_user()
    if current_user:
        if not target:
            target_table = None
        elif inspect.isclass(target):
            target_table = target.__tablename__
        else:
            target_table = target.__tablename__
        if entity_ids and len(entity_ids) > 0:
            values_string_list = []
            for entity_id in entity_ids:
                values_string_list.append(f"""('{action}', {current_user.id}, '{target_table}', {entity_id}, '{str(dt.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.%f"))}')""")
            values_string = ",".join(values_string_list)
            command_string = f"""insert into platform_activity (action, user_id, entity, entity_id, created_at) values {values_string};"""
            connection.execute(command_string)
