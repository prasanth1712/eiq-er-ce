import datetime
import statistics

import requests
from flask import current_app
from requests.auth import HTTPBasicAuth

from polylogyx.extensions import cache


@cache.cached(timeout=120, key_prefix="avg_task_wait_time")
def get_average_celery_task_wait_time():
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
        return statistics.mean(task_wait_time_list)
    except Exception as e:
        current_app.logger.info(
            """Unable to cache the celery task stats of result log processing task, {}""".format(str(e))
        )
        return


@cache.cached(timeout=300, key_prefix="all_configs")
def get_all_configs():
    json = fetch_all_configs()
    return json


def refresh_cached_config():
    json = fetch_all_configs()
    cache.set("all_configs", json)
    return json


def fetch_all_configs():
    from polylogyx.db.models import Config, DefaultFilters, DefaultQuery, db
    from polylogyx.utils.config import assemble_options

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
            db.session.query(DefaultQuery).filter(DefaultQuery.config == None).filter(DefaultQuery.platform == config.platform).filter(DefaultQuery.status).all()
        )
        for default_query in queries:
            schedule[default_query.name] = default_query.to_dict()
        for default_query in version_queries:
            schedule[default_query.name] = default_query.to_dict()
        configs_dict[config.platform][config.name]["schedule"] = schedule
        configs_dict[config.platform][config.name]["options"] = assemble_options(
            configs_dict[config.platform][config.name]
        )
        configs_dict[config.platform][config.name]["cached_at"] = datetime.datetime.utcnow()
    return configs_dict


from polylogyx.utils.log_setting import _get_log_level_from_db

@cache.cached(key_prefix="er_log_level")
def get_log_level():
    level = _get_log_level_from_db()
    return level

def refresh_log_level():
    level = _get_log_level_from_db()
    cache.set("er_log_level", level)