from flask import json
from sqlalchemy import or_, and_

DEFAULT_PLATFORMS = ['windows', 'linux', 'darwin', 'freebsd']
TO_CAPTURE_COLUMNS = ["md5"]
IOC_COLUMNS = ["md5","sha256","domain_name","remote_address","sha1"]


class SystemInfoQueries:

    SYSTEM_STATE_QUERIES = [
        'win_epp_table',
        'patches',
        'os_version',
        'kernel_info',
        'startup_items',
        'drivers',
        'etc_hosts',
        'osquery_info',
        'wmi_cli_event_consumers',
        'wmi_script_event_consumers',
        'users',
        'uptime',
        'certificates',
        'chrome_extensions',
        'ie_extensions',
        'scheduled_tasks',
        'appcompat_shims',
        'powershell_events_script_blocks'
    ]

    SYSTEM_EVENT_QUERIES = [
        'win_file_events',
        'win_process_events',
        'win_process_open_events',
        'win_remote_thread_events',
        'win_pe_file_events',
        'win_removable_media_events',
        'win_http_events',
        'win_socket_events',
        'win_image_load_events',
        'win_dns_events',
        'win_dns_response_events',
        'win_registry_events',
        'win_ssl_events'

    ]


class KernelQueries:
    MAC_ADDRESS_QUERY = "select ia.interface, address,  mac,ibytes, obytes from interface_details id join interface_addresses ia on ia.interface = id.interface where length(mac) > 0 and mac!='00:00:00:00:00:00' order by (ibytes + obytes) desc;"
    KERNEL_VERSION_LINUX_QUERY = """SELECT jsonb_array_elements(data)->>'version' as version,COUNT(jsonb_array_elements(data)->>'version') as count FROM node_data left join node n on n.id=node_id WHERE name='kernel_info' and platform not in  ('windows','darwin') and data::TEXT !='""'::TEXT and data::TEXT !='[]'::TEXT GROUP BY version ORDER BY count DESC LIMIT 1000000;"""
    RMP_DEB_PACKAGES = "SELECT count(*) AS count FROM (SELECT jsonb_array_elements(data)->>'name' as package_name FROM node_data  WHERE name in ('rpm_packages','deb_packages')  and data::TEXT !='\"\"'::TEXT and data::TEXT !='[]'::TEXT LIMIT 1000000) AS expr_qry ;"
    KERNEL_VERSION_QUERY = """SELECT jsonb_array_elements(data)->>'version' as version,COUNT(jsonb_array_elements(data)->>'version') as count FROM node_data left join node n on n.id=node_id WHERE name='kernel_info' and platform = 'windows' and data::TEXT !='""'::TEXT and data::TEXT !='[]'::TEXT GROUP BY version ORDER BY count DESC LIMIT 1000000;"""
    CHROME_IE_EXTENSIONS_QUERY = "SELECT name AS name, count(*) AS count FROM (SELECT jsonb_array_elements(data)->>'path' as path, name FROM node_data WHERE name in ('chrome_extensions', 'ie_extensions') and data::TEXT !='\"\"'::TEXT and data::TEXT !='[]'::TEXT LIMIT 1000000) AS expr_qry GROUP BY name ORDER BY count DESC LIMIT 10000;"
    CHROME_EXTENSIONS_QUERY = "SELECT name AS name, count(*) AS count FROM (SELECT jsonb_array_elements(data)->>'path' as path, name FROM node_data WHERE name in ('chrome_extensions') and data::TEXT !='\"\"'::TEXT and data::TEXT !='[]'::TEXT LIMIT 1000000) AS expr_qry GROUP BY name ORDER BY count DESC LIMIT 10000;"
    CHROME_FIREFOX_EXTENSIONS_QUERY = "SELECT name AS name, count(*) AS count FROM (SELECT jsonb_array_elements(data)->>'path' as path, name FROM node_data left join node n on n.id=node_id WHERE name in ('chrome_extensions', 'firefox_addons') and data::TEXT !='\"\"'::TEXT and platform not in ('windows','darwin') and data::TEXT !='[]'::TEXT LIMIT 1000000) AS expr_qry GROUP BY name ORDER BY count DESC LIMIT 10000;"


class DefaultInfoQueries:

    DEFAULT_QUERIES = {
        "system_info": "select * from system_info;", "os_version": "select * from os_version;",
        "interface_details": KernelQueries.MAC_ADDRESS_QUERY

    }

    DEFAULT_INFO_QUERIES_FREEBSD = {
        "time": "select unix_time, timestamp from time;",
        "etc_hosts": "select * from etc_hosts;"

    }

    DEFAULT_INFO_QUERIES = {
        "win_epp_table": "select * from win_epp_table;",
        "time": "select unix_time, timestamp from time;",
        "certificates": "select common_name, issuer, self_signed, not_valid_after, path from certificates;",
        "etc_hosts": "select * from etc_hosts;",
        "patches": "select hotfix_id, description, installed_on from patches;",
        "kva_speculative_info": "select * from kva_speculative_info;",
        "kernel_info": "select path, version, arguments from kernel_info;",
        "startup_items": "select name, path, status from win_startup_items;",
        "chrome_extensions": "select identifier, version, description, path from chrome_extensions;",
        "scheduled_tasks": "select path, hidden, next_run_time, last_run_message from scheduled_tasks;",
        "win_programs": "select name, version from win_programs;",
        "firefox_addons": "select identifier, version, description, path from firefox_addons;",
        "extensions": "select * from osquery_extensions;",
    }

    DEFAULT_HASHES_QUERY = {
        "win_services": "select ws.module_path,ws.path from win_services ws;",
        "appcompat_shims": "select ach.*,(select sha1 from win_hash wh where wh.path=ach.path limit 1 ) as sha1 from appcompat_shims ach;",
        "ie_extensions": "select iee.path,iee.name,iee.version,(select sha1 from win_hash wh where wh.path=iee.path limit 1 ) as sha1  from ie_extensions iee;",
    }

    DEFAULT_INFO_QUERIES_MACOS = {
        "time": "select unix_time, timestamp from time;",
        "chrome_extensions": "select identifier, version, description, path from chrome_extensions;",
        "kernel_info": "select path, version, arguments from kernel_info;",
        "certificates": "select common_name, issuer, self_signed, not_valid_after, path from certificates;",
        "firefox_addons": "select identifier, version, description, path from firefox_addons;",
        "etc_hosts": "select * from etc_hosts;",
        "startup_items": "select name, path, status from win_startup_items;"
    }

    DEFAULT_INFO_QUERIES_LINUX = {
        "time": "select unix_time, timestamp from time;",
        "kernel_info": "select path, version, arguments from kernel_info;",
        "etc_hosts": "select * from etc_hosts;",
        "chrome_extensions": "select identifier, version, description, path from chrome_extensions;",
        "firefox_addons": "select identifier, version, description, path from firefox_addons;",
        "rpm_packages": "select * from rpm_packages;",
        "deb_packages": "select * from deb_packages;"
    }


class PolyLogyxServerDefaults:
    plgx_config_all_options = "plgx_config_all_options"
    plgx_config_all_settings = "plgx_config_all_settings"
    default_type = "default"
    POLYLOGYX_OSQUERY_SCHEMA_JSON = {}
    search_supporting_columns = ['md5', 'sha256', 'domain_name', 'ja3_md5', 'process_guid', 'parent_process_guid', 'target_path', 'target_name', 'process_name', 'remote_address']


class QueryConstants:
    UNSIGNED_JSON = {"sign_info": "Unsigned"}
    PRODUCT_STATE_QUERY = """SELECT product_type AS product_type,product_state AS product_state,SUM(sum__count) AS product_count
     FROM(SELECT product_type AS product_type, product_state AS product_state,sum(count) AS sum__count 
     FROM (SELECT jsonb_array_elements(data)->>'product_type' as product_type,jsonb_array_elements(data)->>'product_state' as product_state,COUNT(jsonb_array_elements(data)->>'product_state') as count FROM node_data where name='win_epp_table' and data::TEXT !='""'::TEXT and data::TEXT !='[]'::TEXT group by product_type,product_state order by count DESC) AS expr_qry GROUP BY product_type, product_state ORDER BY sum__count DESC LIMIT 10000) AS expr_qry GROUP BY product_type, product_state ORDER BY product_count DESC LIMIT 10000;"""
    PRODUCT_SIGNATURES_QUERY = """SELECT product_type AS product_type,product_signatures AS product_signatures,SUM(sum__count) AS product_count FROM(SELECT product_type AS product_type, product_signatures AS product_signatures,sum(count) AS sum__count FROM (SELECT jsonb_array_elements(data)->>'product_type' as product_type,jsonb_array_elements(data)->>'product_signatures' as product_signatures,COUNT(jsonb_array_elements(data)->>'product_signatures') as count FROM node_data where name='win_epp_table' and data::TEXT !='""'::TEXT and data::TEXT !='[]'::TEXT group by product_type,product_signatures order by count DESC) AS expr_qry GROUP BY product_type, product_signatures ORDER BY sum__count DESC LIMIT 10000) AS expr_qry GROUP BY product_type, product_signatures ORDER BY product_count DESC LIMIT 10000;"""


class EventQueries:
    TOTAL_FILE_EVENTS = "select count(*) from result_log where name like '%win_file_events%';"
    TOTAL_FILE_EVENTS_LINUX = "select count(*) from result_log where name like '%file_events%' and name not like '%win_file_events%' and name not like '%win_pefile_events%';"
    TOTAL_SOCKET_EVENTS_LINUX = "select count(*) from result_log where name like '%socket_events%' and name not like '%win_socket_events%';"


class UtilQueries:
    UNSIGNED_JSON = {"sign_info": "Unsigned"}
    UNSIGNED_BINARY = "SELECT count(*) FROM result_log WHERE name like '%win_image_load_events%' and columns @> '" + json.dumps(UNSIGNED_JSON) + "'; "
    ETC_HOSTS_QUERY = "SELECT  count(*) AS count FROM (SELECT jsonb_array_elements(data)->>'hostnames' as hostnames FROM node_data left join node n on n.id=node_id WHERE name = 'etc_hosts' and platform = 'windows' and data::TEXT !='\"\"'::TEXT and data::TEXT !='[]'::TEXT LIMIT 1000000) AS expr_qry ;"
    ETC_HOSTS_LINUX_QUERY = "SELECT  count(*) AS count FROM (SELECT jsonb_array_elements(data)->>'hostnames' as hostnames FROM node_data left join node n on n.id=node_id WHERE name = 'etc_hosts' and platform not in ('windows','darwin') and data::TEXT !='\"\"'::TEXT and data::TEXT !='[]'::TEXT LIMIT 1000000) AS expr_qry ;"
    TOP_FIVE_PROGRAM = "select columns ->> 'path' as path,count(columns ->> 'path' ) as count from result_log where name like 'win_process_events' and columns ->> 'action'='PROC_CREATE' group by path order by count desc limit 5;"
    BOTTOM_FIVE_PROGRAM = "select columns ->> 'path' as path,count(columns ->> 'path' ) as count from result_log where name like 'win_process_events'  and columns ->> 'action'='PROC_CREATE' group by path order by count  limit 5;"
    TOP_FIVE_PORTS_LINUX = "SELECT columns->>'remote_port' as path, COUNT(columns->>'remote_port') as count  FROM result_log WHERE name like '%socket_events%' and name not like '%win_socket_events%' GROUP BY path ORDER BY count DESC LIMIT 5;"
    TOP_FIVE_IPS_LINUX = "SELECT columns->>'remote_address' as path, COUNT(columns->>'remote_address') as count  FROM result_log WHERE name like '%socket_events%' and name not like '%win_socket_events%' GROUP BY path ORDER BY count DESC LIMIT 5;"
    TOP_FIVE_PROGRAM_LINUX = "select columns ->> 'path' as path,count(columns ->> 'path' ) as count from result_log where name like '%process_events%' and name not like '%win_process_events%' group by path order by count desc limit 5;"
    BOTTOM_FIVE_PROGRAM_LINUX = "select columns ->> 'path' as path,count(columns ->> 'path' ) as count from result_log where name like '%process_events%' and name not like '%win_process_events%'   group by path order by count ASC  limit 5;"
    ALERT_RECON_QUERIES_JSON = {
        "scheduled_queries": [
            {
                "name": "win_file_events",
                "before_event_interval": 30,
                "after_event_interval": 60
            }, {
                "name": "win_process_events",
                "before_event_interval": 30,
                "after_event_interval": 60
            }, {
                "name": "win_registry_events",
                "before_event_interval": 30,
                "after_event_interval": 60
            }, {
                "name": "win_socket_events",
                "before_event_interval": 30,
                "after_event_interval": 60
            }, {
                "name": "win_http_events",
                "before_event_interval": 30,
                "after_event_interval": 60
            }
        ],
        "live_queries": [
            {
                "name": "win_epp_table",
                "query": "select * from win_epp_table;"
            }
        ]
    }


class PlugInQueries:
    VIRUS_TOTAL_QUERY = "select count(*) from virus_total where detections > 0;"
    IBM_THREAT_INTEL_QUERY = "select count(*) from ibm_force_exchange ;"


class ModelStatusFilters:
    from polylogyx.models import Node, Alerts
    HOSTS_ENABLED = and_(Node.state != Node.REMOVED, Node.state != Node.DELETED)
    HOSTS_NON_DELETED = Node.state != Node.DELETED
    HOSTS_DELETED = Node.state == Node.DELETED
    HOSTS_REMOVED = Node.state == Node.REMOVED
    ALERTS_RESOLVED = Alerts.status == Alerts.RESOLVED
    ALERTS_NON_RESOLVED = or_(Alerts.status == None, Alerts.status != Alerts.RESOLVED)


class CacheVariables:
    """
    These can be changes anytime as function refreshes its data when a new name is passed as cache name
    """
    hosts = 'cached_hosts'
    rules = 'cached_rules'
    iocs = 'cached_iocs'
    settings = 'cached_settings'
    user_roles = 'cached_user_roles'
    configs = 'cached_configs'
    avg_task_wait_time = 'avg_task_wait_time'
    rule_network = 'cached_network'
    default_cache_refresh_interval = 3600
