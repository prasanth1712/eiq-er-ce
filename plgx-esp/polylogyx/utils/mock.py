# -*- coding: utf-8 -*-

import os
import sqlite3
import threading
from collections import namedtuple
from os.path import join, dirname

import pkg_resources
from flask import current_app

Field = namedtuple("Field", ["name", "action", "columns", "timestamp", "uuid"])

# Read DDL statements from our package
schema = ''
extension_schema = ''

if os.environ.get('FLASK_ENV') and (os.environ.get('FLASK_ENV') == 'development' or os.environ.get('FLASK_ENV') == 'dev'):
    common_resources_path = join(dirname(dirname(dirname(__file__))), "common")
else:
    common_resources_path = join(dirname(dirname(__file__)), "common")  # This path should be taken from app config

with open(join(common_resources_path, 'osquery_schema.sql'), 'r') as schema_file:
    schema = schema_file.read()

schema = [x for x in schema.strip().split('\n') if not x.startswith('--')]

with open(join(common_resources_path, 'extension_schema.sql'), 'r') as schema_file:
    extension_schema = schema_file.read()

extension_schema = [x for x in extension_schema.strip().split('\n') if not x.startswith('--')]

# SQLite in Python will complain if you try to use it from multiple threads.
# We create a threadlocal variable that contains the DB, lazily initialized.
osquery_mock_db = threading.local()


def create_mock_db():
    from polylogyx.constants import PolyLogyxServerDefaults
    from polylogyx.db.extra_sql_methods import (
        _acos,
        _asin,
        _atan,
        _carve,
        _ceil,
        _community_id_v1,
        _concat,
        _concat_ws,
        _conditional_to_base64,
        _cos,
        _cot,
        _degrees,
        _floor,
        _from_base64,
        _inet_aton,
        _log,
        _log10,
        _pi,
        _power,
        _radians,
        _regex_match,
        _regex_split,
        _sin,
        _split,
        _sqrt,
        _tan,
        _to_base64
    )

    mock_db = sqlite3.connect(":memory:")
    mock_db.create_function("carve", 1, _carve)
    mock_db.create_function("SPLIT", 3, _split)
    mock_db.create_function("concat", -1, _concat)
    mock_db.create_function("concat_ws", -1, _concat_ws)
    mock_db.create_function("regex_split", 3, _regex_split)
    mock_db.create_function("regex_match", 3, _regex_match)
    mock_db.create_function("inet_aton", 1, _inet_aton)
    mock_db.create_function("community_id_v1", -1, _community_id_v1)
    mock_db.create_function("to_base64", 1, _to_base64)
    mock_db.create_function("from_base64", 1, _from_base64)
    mock_db.create_function("conditional_to_base64", 1, _conditional_to_base64)
    mock_db.create_function("sqrt", 1, _sqrt)
    mock_db.create_function("log", 1, _log)
    mock_db.create_function("log10", 1, _log10)
    mock_db.create_function("ceil", 1, _ceil)
    mock_db.create_function("floor", 1, _floor)
    mock_db.create_function("power", 1, _power)
    mock_db.create_function("sin", 1, _sin)
    mock_db.create_function("cos", 1, _cos)
    mock_db.create_function("tan", 1, _tan)
    mock_db.create_function("asin", 1, _asin)
    mock_db.create_function("acos", 1, _acos)
    mock_db.create_function("atan", 1, _atan)
    mock_db.create_function("cot", 1, _cot)
    mock_db.create_function("degrees", 1, _degrees)
    mock_db.create_function("radians", 1, _radians)

    for ddl in schema:
        mock_db.execute(ddl)
    for ddl in extension_schema:
        mock_db.execute(ddl)
    cursor = mock_db.cursor()
    cursor.execute("SELECT name,sql FROM sqlite_master WHERE type='table';")
    for osquery_table in cursor.fetchall():
        PolyLogyxServerDefaults.POLYLOGYX_OSQUERY_SCHEMA_JSON[osquery_table[0]] = osquery_table[1]
    return mock_db


def validate_osquery_query(query):
    # Check if this thread has an instance of the SQLite database
    db = getattr(osquery_mock_db, "db", None)
    if db is None:
        db = create_mock_db()
        osquery_mock_db.db = db

    try:
        db.execute(query)
    except sqlite3.Error:
        current_app.logger.exception("Invalid query: %s", query)
        return False

    return True
