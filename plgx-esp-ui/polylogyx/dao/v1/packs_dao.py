from polylogyx.models import Pack, Tag, db
from sqlalchemy import desc, or_, cast, asc
import sqlalchemy


def get_all_packs(searchterm=''):
    return Pack.query.filter(or_(
            Pack.name.ilike('%' + searchterm + '%'),
            Pack.platform.ilike('%' + searchterm + '%'),
            Pack.version.ilike('%' + searchterm + '%'),
            Pack.description.ilike('%' + searchterm + '%'),
            Pack.category.ilike('%' + searchterm + '%'),
            cast(Pack.shard, sqlalchemy.String).ilike('%' + searchterm + '%'),
        )
        ).order_by(asc(Pack.name))


def get_total_count():
    return Pack.query.count()


def get_pack_by_id(pack_id):
    return Pack.query.filter(Pack.id == pack_id).first()


def get_pack_by_name(name):
    return Pack.query.filter(Pack.name == name).first()


def add_pack(name, category, platform=None, version=None, description=None, shard=None):
    pack = Pack(name=name, category=category, platform=platform, version=version, description=description,
                     shard=shard)
    pack.save()
    return pack


def get_tagged_packs(tag_names):
    return Pack.query.filter(Pack.tags.any(Tag.value.in_(tag_names))).order_by(desc(Pack.id)).all()


def is_tag_of_pack(pack, tag):
    if tag in pack.tags:
        return True
    else:
        return False


def get_all_packs_by_names(packs):
    return db.session.query(Pack).filter(Pack.name.in_(packs)).all()
