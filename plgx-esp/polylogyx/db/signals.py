import datetime as dt
from polylogyx.db.models import Node, Rule, Settings
from polylogyx.utils.cache import remove_cached_host, remove_cached_rule, remove_cached_setting, add_or_update_cached_host, add_or_update_cached_rule, add_or_update_cached_setting


def receive_after_update(mapper, connection, target):
    """
    listen for the 'after_update' event
    """
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
    if type(target) is Node:
        remove_cached_host(node_id=target.id)
    if type(target) is Rule:
        remove_cached_rule(rule_id=target.id)
    if type(target) is Settings:
        remove_cached_setting(setting_name=target.name)
