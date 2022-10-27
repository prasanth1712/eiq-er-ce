# -*- coding: utf-8 -*-
import base64
import datetime as dt
import json
import os
import re
from contextlib import contextmanager
import asyncio

from celery import Celery
from flask import current_app

from polylogyx.constants import PolyLogyxServerDefaults, SettingsVariables
from polylogyx.db.models import (
    CarvedBlock,
    CarveSession,
    DefaultQuery,
    DistributedQuery,
    DistributedQueryTask,
    Node,
    ResultLog,
    NodeQueryCount,
    db
)
from polylogyx.extensions import log_tee, threat_intel

re._pattern_type = re.Pattern

from polylogyx.constants import DefaultInfoQueries


LOCK_EXPIRE = 60 * 2

celery = Celery(__name__)
threat_frequency = 60
celery.conf.update(
    worker_pool_restarts=True,
)


try:
    threat_frequency = int(os.environ.get("THREAT_INTEL_ALERT_FREQUENCY"))
except Exception as e:
    print(e)

celery.conf.beat_schedule = {
    "scan_and_match_with_threat_intel": {
        "task": "polylogyx.celery.tasks.scan_result_log_data_and_match_with_threat_intel",
        "schedule": 300.0,
        "options": {"queue": "default_esp_queue"},
    },
    "send_intel_alerts": {
        "task": "polylogyx.celery.tasks.send_threat_intel_alerts",
        "schedule": threat_frequency * 60,
        "options": {"queue": "default_esp_queue"},
    },
    "send_checkin_queries": {
        "task": "polylogyx.celery.tasks.send_checkin_query_to_all_hosts",
        "schedule": 21600,
        "options": {"queue": "default_esp_queue"},
    },
    "create_daily_partition": {
        "task": "polylogyx.celery.tasks.add_partitions",
        "schedule": 43200,
        "options": {"queue": "default_esp_queue"},
    },
    "update_cached_hosts": {
        "task": "polylogyx.celery.tasks.update_cached_hosts",
        "schedule": 300,
        "options": {"queue": "default_esp_queue"},
    }
}


@contextmanager
def memcache_lock(lock_id, oid):
    import time

    from flask_caching import Cache

    cache = Cache(app=current_app, config={"CACHE_TYPE": "simple"})

    monotonic_time = time.monotonic()
    timeout_at = monotonic_time + LOCK_EXPIRE - 3
    print("in memcache_lock and timeout_at is {}".format(timeout_at))
    # cache.add fails if the key already exists
    status = cache.add(lock_id, oid, LOCK_EXPIRE)
    try:
        yield status
        print("memcache_lock and status is {}".format(status))
    finally:
        # memcache delete is very slow, but we have to use it to take
        # advantage of using add() for atomic locking
        if monotonic_time < timeout_at and status:
            # don't release the lock if we exceeded the timeout
            # to lessen the chance of releasing an expired lock
            # owned by someone else
            # also don't release the lock if we didn't acquire it
            cache.delete(lock_id)


@celery.task()
def add_partitions():
    for i in range(SettingsVariables.pre_create_partitions_count):
        create_daily_partition(day_delay=i)


@celery.task()
def create_daily_partition(day_delay=1):
    import datetime
    try:

        next_day_date = datetime.datetime.today() + datetime.timedelta(days=day_delay)
        next_to_next_day_date = datetime.datetime.today() + datetime.timedelta(days=day_delay + 1)

        next_day_date_string_array = next_day_date.strftime("%b-%d-%Y").split("-")
        next_day_month = next_day_date_string_array[0]
        next_day_date = next_day_date_string_array[1]
        next_day_year = next_day_date_string_array[2]

        partition_start_date = str(next_day_month) + "-" + str(next_day_date) + "-" + str(next_day_year)
        next_to_next_day_date_string_array = next_to_next_day_date.strftime("%b-%d-%Y").split("-")
        next_to_next_day_month = next_to_next_day_date_string_array[0]
        next_to_next_day_date = next_to_next_day_date_string_array[1]
        next_to_next_day_year = next_to_next_day_date_string_array[2]
        partition_end_date = (
                str(next_to_next_day_month) + "-" + str(next_to_next_day_date) + "-" + str(next_to_next_day_year)
        )

        result_log_partition_table = (
                "result_log_" + str(next_day_month) + "_" + str(next_day_date) + "_" + str(next_day_year)
        )

        sql = (
                "CREATE TABLE if not exists "
                + result_log_partition_table
                + " PARTITION OF result_log FOR VALUES FROM ('"
                + partition_start_date
                + "') TO ('"
                + partition_end_date
                + "');"
        )
        pg_trgm_extn="CREATE EXTENSION if not exists pg_trgm;"
        btree_gin_extn="CREATE EXTENSION if not exists btree_gin;"
        
        db.session.execute(pg_trgm_extn)
        db.session.execute(btree_gin_extn)
        db.session.execute(sql)

        create_index_for_result_log(result_log_partition_table)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)


def create_index_for_result_log(result_log_partition_table):
    node_timestamp_desc_index = (
            "CREATE INDEX if not exists idx_"
            + result_log_partition_table
            + "_node_id_timestamp_desc on "
            + result_log_partition_table
            + " (node_id, timestamp DESC NULLS LAST);"
    )

    uuid_index = (
            "CREATE INDEX if not exists idx_"
            + result_log_partition_table
            + "_on_columns_uuid on "
            + result_log_partition_table
            + " (uuid);"
    )
    name_index = (
            "CREATE INDEX if not exists idx_"
            + result_log_partition_table
            + "_name on "
            + result_log_partition_table
            + " (name);"
    )
    time_int_index = (
            "CREATE INDEX if not exists idx_"
            + result_log_partition_table
            + "_on_columns_time_int on "
            + result_log_partition_table
            + " (cast (columns ->> 'time' as integer));"
    )
    md5_index = (
            "CREATE INDEX if not exists idx_"
            + result_log_partition_table
            + "_on_columns_md5 on "
            + result_log_partition_table
            + " ((columns ->> 'md5'));"
    )
    sha256_index = (
            "CREATE INDEX if not exists idx_"
            + result_log_partition_table
            + "_on_columns_sha256 on "
            + result_log_partition_table
            + " ((columns ->> 'sha256'));"
    )
    process_guid_index = (
            "CREATE INDEX if not exists idx_"
            + result_log_partition_table
            + "_on_columns_process_guid on "
            + result_log_partition_table
            + " ((columns ->> 'process_guid'));"
    )
    parent_process_guid_index = (
            "CREATE INDEX if not exists idx_"
            + result_log_partition_table
            + "_on_columns_parent_process_guid on "
            + result_log_partition_table
            + " ((columns ->> 'parent_process_guid'));"
    )
    target_path_index = (
            "CREATE INDEX if not exists idx_"
            + result_log_partition_table
            + "_on_columns_target_path on "
            + result_log_partition_table
            + " ((columns ->> 'target_path'));"
    )
    target_name_index = (
            "CREATE INDEX if not exists idx_"
            + result_log_partition_table
            + "_on_columns_target_name on "
            + result_log_partition_table
            + " ((columns ->> 'target_name'));"
    )
    process_name_index = (
            "CREATE INDEX if not exists idx_"
            + result_log_partition_table
            + "_on_columns_process_name on "
            + result_log_partition_table
            + " ((columns ->> 'process_name'));"
    )
    remote_address_index = (
            "CREATE INDEX if not exists idx_"
            + result_log_partition_table
            + "_on_columns_remote_address on "
            + result_log_partition_table
            + " ((columns ->> 'remote_address'));"
    )
    event_id_index = (
            "CREATE INDEX if not exists idx_"
            + result_log_partition_table
            + "_on_columns_eventid on "
            + result_log_partition_table
            + " ((columns ->> 'eventid'));"
    )

    rl_id_index = (
            "CREATE INDEX if not exists idx_"
            + result_log_partition_table
            + "_id on "
            + result_log_partition_table
            + " (id);"
    )



    index_sqls = [
        node_timestamp_desc_index,
        uuid_index,
        name_index,
        time_int_index,
        md5_index,
        sha256_index,
        process_guid_index,
        parent_process_guid_index,
        target_path_index,
        target_name_index,
        process_name_index,
        remote_address_index,
        event_id_index,
        rl_id_index,
    ]
    # Adding indexes of Result log to all partitions
    for sql in index_sqls:
        db.session.execute(sql)
    db.session.commit()


def profiler(func):
    def inner(*args, **kwargs):
        import cProfile
        pr = cProfile.Profile()
        pr.enable()
        func(*args, **kwargs)
        pr.disable()
        name = func.__name__
        pr.dump_stats(name)
    return inner


def update_node_query_count(query_count_list, node_id):
    # to form list of dictionaries for bulk update objects
    create_list = []
    update_list = []
    node_query_counts = db.session.query(NodeQueryCount).filter(NodeQueryCount.node_id == node_id).filter(
        NodeQueryCount.query_name.in_(list(query_count_list.keys()))).all()
    for query_name, count in query_count_list.items():
        if isinstance(count, int):
            found = False
            for item in node_query_counts:
                if item.query_name == query_name and item.event_id is None and \
                        item.date.date() == dt.datetime.now().date():
                    update_list.append({'query_name': query_name, 'total_results': item.total_results+count,
                                        'node_id': node_id, 'date': dt.datetime.now().date(), 'id': item.id})
                    found = True
                    break
            if not found:
                create_list.append({'query_name': query_name, 'total_results': count, 'node_id': node_id,
                                    'date': dt.datetime.now().date()})
        else:
            for event_id, count_value in count.items():
                found = False
                for item in node_query_counts:
                    if item.query_name == query_name and item.event_id == event_id and \
                            item.date.date() == dt.datetime.now().date():
                        update_list.append({'query_name': query_name, 'total_results': item.total_results+count_value,
                                            'node_id': node_id, 'date': dt.datetime.now().date(), 'event_id': event_id,
                                            'id': item.id})
                        found = True
                        break
                if not found:
                    create_list.append({'query_name': query_name, 'total_results': count_value,
                                        'event_id': event_id, 'node_id': node_id, 'date': dt.datetime.now().date()})
    db.session.bulk_insert_mappings(NodeQueryCount, create_list)
    db.session.bulk_update_mappings(NodeQueryCount, update_list)


def save_result_log_def(results, query_count_list, node_dict):
    db.session.bulk_insert_mappings(ResultLog, results)
    update_node_query_count(query_count_list, node_dict['id'])
    db.session.commit()


async def start_async_tasks(results, query_count_list, node_dict):
    save_log = os.environ.get('SAVE_LOG')
    match_rule = os.environ.get('MATCH_RULE')
    match_ioc = os.environ.get('MATCH_IOC')
    rule_eng_task = None
    ioc_eng_task = None
    if save_log and query_count_list and results and node_dict:
        save_result_log_def(results, query_count_list, node_dict)
    if match_rule and results and node_dict:
        rule_eng_task = asyncio.create_task(current_app.rule_manager.handle_log_entry(results, node_dict))
    if match_ioc and results and node_dict:
        ioc_eng_task = asyncio.create_task(current_app.ioc_engine.process(node_dict['id'], results))
    if rule_eng_task:
        await rule_eng_task
    if ioc_eng_task:
        await ioc_eng_task


@celery.task()
def save_analyze(results, query_count_list, node_dict):
    asyncio.run(start_async_tasks(results=results, query_count_list=query_count_list, node_dict=node_dict))


@celery.task()
def save_analyze_rules(results, query_count_list, node_dict):
    asyncio.run(start_async_tasks(results=results, query_count_list=query_count_list, node_dict=node_dict))


@celery.task()
def save_analyze_iocs(results, query_count_list, node_dict):
    asyncio.run(start_async_tasks(results=results, query_count_list=query_count_list, node_dict=node_dict))


@celery.task()
def analyze_rules_and_ioc(results, node_dict):
    asyncio.run(start_async_tasks(results=results, query_count_list=None, node_dict=node_dict))


@celery.task()
def save_result_log(results, query_count_list, node_dict):
    asyncio.run(start_async_tasks(results=results, query_count_list=query_count_list, node_dict=node_dict))


@celery.task()
def analyze_rules(results, node_dict):
    asyncio.run(start_async_tasks(results=results, query_count_list=None, node_dict=node_dict))


@celery.task()
def analyze_ioc(results, node_dict):
    asyncio.run(start_async_tasks(results=results, query_count_list=None, node_dict=node_dict))


def analyze_result(results, query_count_list, node_dict):
    save_log_queue = current_app.config.get('INI_CONFIG', {}).get('save_log_queue')
    match_rule_queue = current_app.config.get('INI_CONFIG', {}).get('match_rule_queue')
    match_ioc_queue = current_app.config.get('INI_CONFIG', {}).get('match_ioc_queue')

    if save_log_queue is not None and save_log_queue == match_rule_queue == match_ioc_queue:
        if save_log_queue !=  'result_log_queue':
            save_analyze.apply_async(queue=save_log_queue, args=[results, query_count_list, node_dict])
        else:
            save_analyze(results, query_count_list, node_dict)
    elif save_log_queue is not None and save_log_queue == match_rule_queue:
        if save_log_queue !=  'result_log_queue':
            save_analyze_rules.apply_async(queue=save_log_queue, args=[results, query_count_list, node_dict])
        else:
            save_analyze_rules(results, query_count_list, node_dict)
        if match_ioc_queue != 'result_log_queue':
            analyze_ioc.apply_async(queue=match_ioc_queue, args=[results, node_dict])
        else:
            analyze_ioc(results, node_dict)
    elif save_log_queue is not None and save_log_queue == match_ioc_queue:
        if save_log_queue !=  'result_log_queue':
            save_analyze_iocs.apply_async(queue=save_log_queue, args=[results, query_count_list, node_dict])
        else:
            save_analyze_iocs(results, query_count_list, node_dict)
        if match_rule_queue != 'result_log_queue':
            analyze_rules.apply_async(queue=match_rule_queue, args=[results, node_dict])
        else:
            analyze_rules(results, node_dict)
    elif match_rule_queue is not None and match_rule_queue == match_ioc_queue:
        if save_log_queue != 'result_log_queue':
            save_result_log.apply_async(queue=save_log_queue, args=[results, query_count_list, node_dict])
        else:
            save_result_log(results, query_count_list, node_dict)
        if match_rule_queue != 'result_log_queue':
            analyze_rules_and_ioc.apply_async(queue=match_rule_queue, args=[results, node_dict])
        else:
            analyze_rules_and_ioc(results, node_dict)
    else:
        if save_log_queue is not None:
            if save_log_queue != 'result_log_queue':
                save_result_log.apply_async(queue=save_log_queue, args=[results, query_count_list, node_dict])
            else:
                save_result_log(results, query_count_list, node_dict)
        if match_rule_queue is not None:
            if match_rule_queue != 'result_log_queue':
                analyze_rules.apply_async(queue=match_rule_queue, args=[results, node_dict])
            else:
                analyze_rules(results, node_dict)
        if match_ioc_queue is not None:
            if match_ioc_queue != 'result_log_queue':
                analyze_ioc.apply_async(queue=match_ioc_queue, args=[results, node_dict])
            else:
                analyze_ioc(results, node_dict)


@celery.task()
def save_and_analyze_results(data, node_dict):
    from polylogyx.utils.results import process_result
    from polylogyx.utils.cache import update_cached_host

    current_app.logger.debug("Parsing the results for the node '{0}'".format([node_dict['hostname']]))
    results, query_count_list, node_host_details_to_update = process_result(data, node_dict)
    current_app.logger.debug("Saved the results successfully for the node '{0}'".format(node_dict['hostname']))
    analyze_result(results, query_count_list, node_dict)
    log_tee.handle_result(results, host_identifier=node_dict['host_identifier'], node=node_dict)
    if node_host_details_to_update:
        update_cached_host(node_dict['node_key'], {'host_details': node_host_details_to_update})


@celery.task()
def learn_from_result(result, node):
    from polylogyx.utils.results import learn_from_result

    learn_from_result(result, node)
    return


@celery.task()
def build_carve_session_archive(session_id):
    from polylogyx.db.models import db

    carve_session = CarveSession.query.filter(CarveSession.session_id == session_id).first_or_404()
    if carve_session.archive:
        current_app.logger.error("Archive already exists for session %s", session_id)
        return

    # build archive file from carve blocks

    out_file_name = session_id + carve_session.carve_guid
    # Check the first four bytes for the zstd header. If not no
    # compression was used, it's a generic .tar
    carve_block_data = (
        db.session.query(CarvedBlock.data).filter(CarvedBlock.session_id == session_id).order_by("block_id").all()
    )
    if base64.standard_b64decode(carve_block_data[0][0])[0:4] == b"\x28\xB5\x2F\xFD":
        out_file_name += ".zst"
    else:
        out_file_name += ".tar"
    carve_session.archive = out_file_name

    out_file_name = (
        os.path.join(current_app.config.get('RESOURCES_URL'), 'carves', carve_session.node.host_identifier, out_file_name)
    )
    if not os.path.exists(os.path.join(current_app.config.get('RESOURCES_URL'), 'carves', carve_session.node.host_identifier)):
        os.makedirs(os.path.join(current_app.config.get('RESOURCES_URL'), 'carves', carve_session.node.host_identifier))
    with open(out_file_name, "wb") as f:
        for data in carve_block_data:
            f.write(base64.standard_b64decode(data[0]))
    carve_session.status = CarveSession.StatusCompleted
    carve_session.update(carve_session)
    db.session.commit()


@celery.task()
def example_task(one, two):
    print("Adding {0} and {1}".format(one, two))
    return one + two


@celery.task()
def send_recon_on_checkin(node_dict):
    try:
        send_queries(node_dict)
    except Exception as e:
        current_app.logger.error(e)


@celery.task()
def scan_result_log_data_and_match_with_threat_intel():

    try:
        lock_id = "scanResultLogDataAndMatchWithThreatIntel"

        with memcache_lock(lock_id, "polylogyx") as acquired:
            if acquired:
                threat_intel.update_credentials()
                threat_intel.analyse_pending_hashes()
    except Exception as e:
        current_app.logger.error(e)


@celery.task()
def send_threat_intel_alerts():
    threat_intel.generate_alerts()


def clear_new_queries(node_dict):
    try:
        db.session.query(DistributedQueryTask).filter(DistributedQueryTask.node_id == node_dict['id']).filter(
            DistributedQueryTask.save_results_in_db == True
        ).filter(DistributedQueryTask.status == DistributedQueryTask.NEW).update(
            {"status": DistributedQueryTask.NOT_SENT}
        )
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)


def send_queries(node_dict):
    clear_new_queries(node_dict)
    try:
        for key, value in DefaultInfoQueries.DEFAULT_QUERIES.items():
            query = DistributedQuery.create(
                sql=value,
                description=key,
            )
            task = DistributedQueryTask(node_id=node_dict['id'], distributed_query=query, save_results_in_db=True)
            db.session.add(task)

        for key, value in DefaultInfoQueries.DEFAULT_VERSION_INFO_QUERIES.items():
            platform = node_dict['platform']
            if platform not in ["windows", "darwin", "freebsd"]:
                platform = "linux"
            default_query = (
                DefaultQuery.query.filter(DefaultQuery.name == key).first()
            )
            if default_query:
                query = DistributedQuery.create(sql=default_query.sql, description=value)
                task = DistributedQueryTask(node_id=node_dict['id'], distributed_query=query, save_results_in_db=True)
                db.session.add(task)
        for key, value in DefaultInfoQueries.DEFAULT_DEFENDER_INFO_QUERY.items():
            platform = node_dict['platform']
            if platform == "windows":
                default_query = (
                    DefaultQuery.query.filter(DefaultQuery.name == key)
                    .first()
                )
                if default_query:
                    query = DistributedQuery.create(sql=default_query.sql, description=value)
                    task = DistributedQueryTask(node_id=node_dict['id'], distributed_query=query, save_results_in_db=True)
                    db.session.add(task)
        db.session.commit()

    except Exception as e:
        current_app.logger.error(e)


@celery.task()
def send_checkin_query_to_all_hosts():
    from polylogyx.utils.cache import get_all_cached_hosts

    nodes = get_all_cached_hosts()
    for node_key, node_dict in nodes.items():
        send_queries(node_dict)


@celery.task()
def update_cached_hosts():
    from polylogyx.utils.cache import get_all_cached_hosts, remove_cached_host

    hosts = get_all_cached_hosts()
    node_keys_from_db = [node.node_key for node in Node.query.with_entities(Node.node_key).all()]
    final_hosts = {}
    for node_key, node_dict in hosts.items():
        for column, value in node_dict.items():
            if node_key in node_keys_from_db:
                if value is not None:
                    if node_key in final_hosts:
                        final_hosts[node_key][column] = value
                    else:
                        final_hosts[node_key] = {column: value}
            else:
                remove_cached_host(node_key=node_key)
                
    db.session.bulk_update_mappings(Node, list(final_hosts.values()))
    db.session.commit()
