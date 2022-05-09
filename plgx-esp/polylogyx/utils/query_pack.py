# -*- coding: utf-8 -*-
import ast
import json
from os.path import basename, splitext

import six
from flask import current_app, flash

from polylogyx.db.models import Pack, Query
from polylogyx.utils.mock import validate_osquery_query


def create_query_pack_from_upload(upload):
    """
    Create a pack and queries from a query pack file. **Note**, if a
    pack already exists under the filename being uploaded, then any
    queries defined here will be added to the existing pack! However,
    if a query with a particular name already exists, and its sql is
    NOT the same, then a new query with the same name but different id
    will be created (as to avoid clobbering the existing query). If its
    sql is identical, then the query will be reused.

    """
    # The json package on Python 3 expects a `str` input, so we're going to
    # read the body and possibly convert to the right type
    body = upload.data.read()
    if not isinstance(body, six.string_types):
        body = body.decode("utf-8")

    try:
        data = json.loads(body)
    except ValueError:
        flash(u"Could not load pack as JSON - ensure it is JSON encoded", "danger")
        return None
    else:
        if "queries" not in data:
            flash(u"No queries in pack", "danger")
            return None

        name = splitext(basename(upload.data.filename))[0]
        pack = Pack.query.filter(Pack.name == name).first()

    if not pack:
        current_app.logger.debug("Creating pack %s", name)
        pack = Pack.create(name=name, **data)

    for query_name, query in data["queries"].items():
        if not validate_osquery_query(query["query"]):
            flash('Invalid osquery query: "{0}"'.format(query["query"]), "danger")
            return None

        q = Query.query.filter(Query.name == query_name).first()

        if not q:
            q = Query.create(name=query_name, **query)
            pack.queries.append(q)
            current_app.logger.debug("Adding new query %s to pack %s", q.name, pack.name)
            continue

        if q in pack.queries:
            continue

        if q.sql == query["query"]:
            current_app.logger.debug("Adding existing query %s to pack %s", q.name, pack.name)
            pack.queries.append(q)
        else:
            q2 = Query.create(name=query_name, **query)
            current_app.logger.debug(
                "Created another query named %s, but different sql: %r vs %r",
                query_name,
                q2.sql.encode("utf-8"),
                q.sql.encode("utf-8"),
            )
            pack.queries.append(q2)

    else:
        pack.save()
        flash(u"Imported query pack {0}".format(pack.name), "success")

    return pack
