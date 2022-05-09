# -*- coding: utf-8 -*-
import base64
import datetime as dt
import json
import os
import re
from contextlib import contextmanager

from celery import Celery
from flask import current_app

from polylogyx.constants import PolyLogyxServerDefaults
from polylogyx.db.models import (
    CarvedBlock,
    CarveSession,
    DefaultQuery,
    DistributedQuery,
    DistributedQueryTask,
    Node,
    ResultLog,
    db
)
from polylogyx.extensions import log_tee, threat_intel

re._pattern_type = re.Pattern

from polylogyx.constants import DefaultInfoQueries
from polylogyx.db.models import DefaultQuery, DistributedQuery, DistributedQueryTask, Node

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
    "send_defender_info_query": {
        "task": "polylogyx.celery.tasks.send_defender_info_query",
        "schedule": 3600,
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
def analyze_result(result, node):
    # learn_from_result.s(result, node).delay()
    current_app.rule_manager.handle_log_entry(result, node)
    return


@celery.task()
def add_partitions():
   for i in range(7):
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
        node_query_count_partition_table = (
                "node_query_count_" + str(next_day_month) + "_" + str(next_day_date) + "_" + str(next_day_year)
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
        db.session.execute(sql)
        create_index_and_trigger(result_log_partition_table, node_query_count_partition_table)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)


def create_index_and_trigger(result_log_partition_table,node_query_count_partition_table):
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
    ]
    # Adding indexes of Result log to all partitions
    for sql in index_sqls:
        db.session.execute(sql)

    trigger_string = (
            """CREATE or REPLACE FUNCTION """
            + node_query_count_partition_table
            + """() RETURNS trigger
        LANGUAGE plpgsql AS
     $$ BEGIN                                                                                                                                                             
         IF TG_OP = 'INSERT' and NEW.action != 'removed' THEN 
             IF NEW.name != 'windows_real_time_events' THEN                                                                                                          
                 UPDATE node_query_count SET total_results = total_results + 1 where node_id=NEW.node_id and query_name=NEW.name and date=date_trunc('day', NEW.created_at) ;
             ELSE
                 UPDATE node_query_count SET total_results=total_results+1 WHERE node_id=NEW.node_id and query_name=NEW.name and event_id=NEW.columns->>'eventid'and date=date_trunc('day', NEW.created_at);
                 END IF;
             IF found THEN 

                  RETURN NEW;                                                                                                                                           
             END IF; 

             BEGIN
                     IF NEW.name != 'windows_real_time_events' THEN
                         INSERT INTO  node_query_count(node_id, query_name, total_results,date) VALUES (NEW.node_id, NEW.name, 1,date_trunc('day', NEW.created_at));
                     ELSE
                         INSERT INTO  node_query_count(node_id, query_name, event_id, total_results,date) VALUES (NEW.node_id, NEW.name, NEW.columns->>'eventid', 1,date_trunc('day', NEW.created_at));
                     END IF;
                     RETURN NEW;                                                                                                                                                                                                                                                                                        

             END;                                                                                                                                                       
         ELSIF TG_OP = 'DELETE' and OLD.action != 'removed' THEN  
             IF OLD.name != 'windows_real_time_events' THEN
                     UPDATE node_query_count SET total_results=total_results-1 WHERE node_id=OLD.node_id and query_name=OLD.name and date=date_trunc('day', OLD.created_at);
             ELSE
                     UPDATE node_query_count SET total_results=total_results-1 WHERE node_id=OLD.node_id and query_name=OLD.name and event_id=OLD.columns->>'eventid' and date=date_trunc('day', OLD.created_at);
                 END IF;
                 DELETE from node_query_count WHERE total_results=0;
                 RETURN OLD;

         ELSE                                                                                                                                                           
            UPDATE node_query_count SET total_results = 0 where node_id=NEW.node_id and query_name=NEW.name;                                                                                                                                                                                                                        
            RETURN NULL;                                                                                                                                                
         END IF;                                                                                                                                                        
      END;$$;
      """
    )
    db.session.execute(trigger_string)

    check_trg_name = str(node_query_count_partition_table)+"_mod"
    check_if_trigger_exists = "select count(*) from pg_trigger where lower(tgname)='{}'".format(check_trg_name.lower())
    res = db.session.execute(check_if_trigger_exists).first()[0]

    if res==0:
        trigger_mod_string = (
                """
            CREATE  CONSTRAINT TRIGGER """
                + node_query_count_partition_table
                + """_mod
        AFTER INSERT OR DELETE ON """
                + result_log_partition_table
                + """
        DEFERRABLE INITIALLY DEFERRED
        FOR EACH ROW EXECUTE PROCEDURE """
                + node_query_count_partition_table
                + """();
        """
        )
        db.session.execute(trigger_mod_string)

    check_trg_name = str(node_query_count_partition_table)+"_trunc"
    check_if_trigger_exists = "select count(*) from pg_trigger where lower(tgname)='{}'".format(check_trg_name.lower())
    res = db.session.execute(check_if_trigger_exists).first()[0]

    if res==0:
        trigger_truncate = (
                """
            CREATE TRIGGER """
                + node_query_count_partition_table
                + """_trunc AFTER TRUNCATE ON """
                + result_log_partition_table
                + """
        FOR EACH STATEMENT EXECUTE PROCEDURE """
                + node_query_count_partition_table
                + """();
        """
        )
        db.session.execute(trigger_truncate)

    db.session.commit()


@celery.task()
def save_and_analyze_results(data, node_id):
    from polylogyx.utils.results import process_result

    node = db.session.query(Node).filter(Node.id == node_id).first()
    current_app.logger.debug("Parsing the results for the node '{0}'".format(node))
    results = process_result(data, node)
    db.session.bulk_insert_mappings(ResultLog, results)
    db.session.commit()
    current_app.logger.debug("Saved the results successfully for the node '{0}'".format(node))
    log_tee.handle_result(results, host_identifier=node.host_identifier, node=node.to_dict())
    analyze_result(results, node.to_dict())
    return


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
        PolyLogyxServerDefaults.BASE_URL + "/carves/" + carve_session.node.host_identifier + "/" + out_file_name
    )
    if not os.path.exists(PolyLogyxServerDefaults.BASE_URL + "/carves/" + carve_session.node.host_identifier + "/"):
        os.makedirs(PolyLogyxServerDefaults.BASE_URL + "/carves/" + carve_session.node.host_identifier + "/")
    f = open(out_file_name, "wb")

    for data in carve_block_data:
        f.write(base64.standard_b64decode(data[0]))
    # break;
    f.close()
    carve_session.status = CarveSession.StatusCompleted
    carve_session.update(carve_session)
    db.session.commit()


@celery.task()
def example_task(one, two):
    print("Adding {0} and {1}".format(one, two))
    return one + two


@celery.task()
def send_recon_on_checkin(node):
    from polylogyx.db.database import db

    try:
        node_obj = Node.query.filter(Node.id == node.get("id")).first()
        send_queries(node_obj, db)
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


def clear_new_queries(node, db):
    try:
        db.session.query(DistributedQueryTask).filter(DistributedQueryTask.node_id == node.id).filter(
            DistributedQueryTask.save_results_in_db == True
        ).filter(DistributedQueryTask.status == DistributedQueryTask.NEW).update(
            {"status": DistributedQueryTask.NOT_SENT}
        )
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)


def is_extension_old(node):
    return (
        "extension_version" in node.host_details
        and node.host_details["extension_version"]
        and node.host_details["extension_version"].startswith("1")
    )


def send_queries(node, db):
    clear_new_queries(node, db)
    try:
        for key, value in DefaultInfoQueries.DEFAULT_QUERIES.items():
            query = DistributedQuery.create(
                sql=value,
                description=key,
            )
            task = DistributedQueryTask(node=node, distributed_query=query, save_results_in_db=True)
            db.session.add(task)

        for key, value in DefaultInfoQueries.DEFAULT_VERSION_INFO_QUERIES.items():
            if key == DefaultInfoQueries.EXTENSION_HASH_QUERY_NAME and not is_extension_old(node):
                continue
            platform = node.platform
            if platform not in ["windows", "darwin", "freebsd"]:
                platform = "linux"
            default_query = (
                DefaultQuery.query.filter(DefaultQuery.name == key).filter(DefaultQuery.platform == platform).first()
            )
            if default_query:
                query = DistributedQuery.create(sql=default_query.sql, description=value)
                task = DistributedQueryTask(node=node, distributed_query=query, save_results_in_db=True)
                db.session.add(task)
        for key, value in DefaultInfoQueries.DEFAULT_DEFENDER_INFO_QUERY.items():
            platform = node.platform
            if platform == "windows":
                default_query = (
                    DefaultQuery.query.filter(DefaultQuery.name == key)
                    .filter(DefaultQuery.platform == platform)
                    .first()
                )
                if default_query:
                    query = DistributedQuery.create(sql=default_query.sql, description=value)
                    task = DistributedQueryTask(node=node, distributed_query=query, save_results_in_db=True)
                    db.session.add(task)
        db.session.commit()

    except Exception as e:
        current_app.logger.error(e)


@celery.task()
def send_defender_info_query():
    from polylogyx.db.database import db

    nodes = Node.query.all()
    active_nodes = []
    host_identifiers = []
    for node in nodes:
        if node.node_is_active() and node.platform == "windows":
            active_nodes.append(node)
            host_identifiers.append(node.host_identifier)
    defender_status_check(active_nodes, db)


def defender_status_check(nodes, db):
    try:
        for key, value in DefaultInfoQueries.DEFAULT_DEFENDER_INFO_QUERY.items():
            default_query = DefaultQuery.query.filter(DefaultQuery.name == key).first()
            query = DistributedQuery.create(sql=default_query.sql, description=value)
            for node in nodes:
                task = DistributedQueryTask(node=node, distributed_query=query, save_results_in_db=True)
                db.session.add(task)
            db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
    return


@celery.task()
def send_checkin_query_to_all_hosts():
    from polylogyx.db.models import db

    nodes = Node.query.all()
    for node in nodes:
        send_queries(node, db)
