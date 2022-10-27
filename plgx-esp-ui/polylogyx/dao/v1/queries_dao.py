from polylogyx.models import Query, db, Pack, Tag
from polylogyx.utils import create_tags
from sqlalchemy import desc, asc, or_, cast
import sqlalchemy


def get_total_count():
    return Query.query.count()


def get_total_packed_queries_count():
    return Query.query \
        .options(
        db.joinedload(Query.tags),
        db.joinedload(Query.packs),
        db.joinedload(Query.packs, Pack.queries, innerjoin=True)
    ).filter(Query.packs.any()).count()


def get_query_by_name(query_name):
    return Query.query.filter(Query.name == query_name).first()


def add_query(query_name, **query):
    return Query.create(name=query_name, **query)


def get_all_queries(searchterm=''):
    queries = Query.query \
        .options(
        db.joinedload(Query.tags),
        db.joinedload(Query.packs),
        db.joinedload(Query.packs, Pack.queries, innerjoin=True)).filter(Query.name.ilike('%' + searchterm + '%')).order_by(asc(Query.name))
    return queries


def get_all_packed_queries(searchterm=''):
    queries = Query.query \
        .options(
        db.joinedload(Query.tags),
        db.joinedload(Query.packs),
        db.joinedload(Query.packs, Pack.queries, innerjoin=True)
    ).filter(Query.packs.any()).filter(
            Query.name.ilike('%' + searchterm + '%')).order_by(asc(Query.name))
    return queries


def get_query_by_id(query_id):
    return Query.query.options(
                db.joinedload(Query.tags)
            ).filter(Query.id == query_id).first()


def create_query_obj(name,sql,interval,platform,version,description,value,shard,snapshot=False):
    return Query(name=name,sql=sql,interval=interval,platform=platform,version=version,description=description,value=value,shard=shard,snapshot=snapshot)


def get_tagged_queries(tag_names):
    return Query.query.filter(Query.tags.any(Tag.value.in_(tag_names))).order_by(desc(Query.id)).all()


def edit_query_by_id(query, args):
    from polylogyx.dao.v1 import packs_dao
    tags = create_tags(*args['tags'])
    packs = []
    if args['packs']:
        packs = args['packs'].split(',')
    packs_list = []
    for pack_name in packs:
        pack = packs_dao.get_pack_by_name(pack_name)
        if pack:
            packs_list.append(pack)
    return query.update(name=args['name'], sql=args['query'], interval=args['interval'], tags=tags, platform=args['platform'], version=args['version'], description=args['description'], value=args['value'], snapshot=args['snapshot'], packs=packs_list)


def is_tag_of_query(query, tag):
    if tag in query.tags:
        return True
    else:
        return False


def get_all_queries_by_names(queries):
    return db.session.query(Query).filter(Query.name.in_(queries)).all()
