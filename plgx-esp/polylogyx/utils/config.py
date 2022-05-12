# -*- coding: utf-8 -*-

import datetime as dt
import json

from flask import current_app

from polylogyx.constants import DEFAULT_PLATFORMS, DefaultInfoQueries, PolyLogyxServerDefaults
from polylogyx.db.database import db
from polylogyx.db.models import (
    DefaultFilters,
    DefaultQuery,
    DistributedQuery,
    DistributedQueryTask,
    Node,
    NodeConfig,
    Options,
    Pack,
    Query,
    querypacks
)
from polylogyx.utils.generic import merge_two_dicts
from polylogyx.utils.node import get_config_of_node


def get_node_configuration(node):
    from polylogyx.utils.cache import get_all_configs, refresh_cached_config

    platform = node.platform
    if platform not in DEFAULT_PLATFORMS:
        platform = "linux"
    config = get_config_of_node(node)
    # get all cached configs
    all_configs = get_all_configs()
    configuration = all_configs.get(platform, {}).get(config.name, {})
    if not configuration:
        all_configs = refresh_cached_config()
        configuration = all_configs.get(platform, {}).get(config.name, {})
        if not configuration:
            current_app.logger.warning("Could not find config assigned to the node '{}'".format(node))
    else:
        cached_at = configuration.get("cached_at")
        if cached_at and cached_at < config.updated_at:
            # refresh cached config when there is an update in the config
            all_configs = refresh_cached_config()
            configuration = all_configs.get(platform, {}).get(config.name, {})
            if not configuration:
                current_app.logger.warning("Could not find config assigned to the node '{}'".format(node))
    if isinstance(configuration, dict) and 'cached_at' in configuration:
        configuration.pop("cached_at")
    return configuration


def assemble_configuration(node):
    from polylogyx.celery.tasks import is_extension_old

    configuration = get_node_configuration(node)
    if node.tags:
        # assemble extra queries added(not default queries)
        for query in node.queries.options(db.lazyload("*")):
            configuration["schedule"][query.name] = query.to_dict()
        configuration["packs"] = assemble_packs(node)
    if (
        "schedule" in configuration
        and DefaultInfoQueries.EXTENSION_HASH_QUERY_NAME in configuration["schedule"]
        and not is_extension_old(node)
    ):
        del configuration["schedule"][DefaultInfoQueries.EXTENSION_HASH_QUERY_NAME]
    return configuration


def assemble_options(configuration):
    options = {"disable_watchdog": True, "logger_tls_compress": True}

    # https://github.com/facebook/osquery/issues/2048#issuecomment-219200524
    if current_app.config["POLYLOGYX_EXPECTS_UNIQUE_HOST_ID"]:
        options["host_identifier"] = "uuid"
    else:
        options["host_identifier"] = "hostname"

    options["schedule_splay_percent"] = 10
    existing_option = Options.query.filter(Options.name == PolyLogyxServerDefaults.plgx_config_all_options).first()
    if existing_option:
        existing_option_value = json.loads(existing_option.option)
        options = merge_two_dicts(options, existing_option_value)
    options.update(configuration.get("options", {}))
    return options


def assemble_packs(node):
    packs = {}
    for pack in node.packs.join(querypacks).join(Query).options(db.contains_eager(Pack.queries)).all():
        packs[pack.name] = pack.to_dict()
    return packs


def assemble_distributed_queries(node):
    """
    Retrieve all distributed queries assigned to a particular node
    in the NEW state. This function will change the state of the
    distributed query to PENDING, however will not commit the change.
    It is the responsibility of the caller to commit or rollback on the
    current database session.
    """
    now = dt.datetime.utcnow()
    pending_query_count = 0
    query_recon_count = db.session.query(db.func.count(DistributedQueryTask.id)).filter(
        DistributedQueryTask.node == node,
        DistributedQueryTask.status == DistributedQueryTask.NEW,
        DistributedQueryTask.priority == DistributedQueryTask.HIGH,
    )
    for r in query_recon_count:
        pending_query_count = r[0]
    if pending_query_count > 0:
        query = (
            db.session.query(DistributedQueryTask)
            .join(DistributedQuery)
            .filter(
                DistributedQueryTask.node == node,
                DistributedQueryTask.status == DistributedQueryTask.NEW,
                DistributedQuery.not_before < now,
                DistributedQueryTask.priority == DistributedQueryTask.HIGH,
            )
            .options(db.lazyload("*"), db.contains_eager(DistributedQueryTask.distributed_query))
        )
    else:
        query = (
            db.session.query(DistributedQueryTask)
            .join(DistributedQuery)
            .filter(
                DistributedQueryTask.node == node,
                DistributedQueryTask.status == DistributedQueryTask.NEW,
                DistributedQuery.not_before < now,
                DistributedQueryTask.priority == DistributedQueryTask.LOW,
            )
            .options(db.lazyload("*"), db.contains_eager(DistributedQueryTask.distributed_query))
            .limit(1)
        )

    queries = {}
    for task in query:
        if task.sql:
            queries[task.guid] = task.sql
        else:
            queries[task.guid] = task.distributed_query.sql
        task.update(
            status=DistributedQueryTask.PENDING,
            viewed_at=dt.datetime.utcnow(),
            updated_at=dt.datetime.utcnow(),
            commit=False,
        )

        # add this query to the session, but don't commit until we're
        # as sure as we possibly can be that it's been received by the
        # osqueryd client. unfortunately, there are no guarantees though.
        db.session.add(task)
    return queries
