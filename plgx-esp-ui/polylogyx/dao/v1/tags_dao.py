from polylogyx.models import Tag
from sqlalchemy import desc
from flask import current_app
from polylogyx.blueprints.v1.utils import *


def get_all_tags(searchterm="",order_by=None):
    if order_by == 'desc':
        return Tag.query.filter(Tag.value.ilike('%' + searchterm + '%')).order_by(desc(Tag.value))
    elif order_by == 'asc':
        return Tag.query.filter(Tag.value.ilike('%' + searchterm + '%')).order_by(Tag.value)
    return Tag.query.filter(Tag.value.ilike('%' + searchterm + '%')).order_by(desc(Tag.id))


def get_tags_total_count():
    return Tag.query.count()


def delete_tag(tag):
    tag.delete()


def create_tag_obj(tag):
    tag_existing = Tag.query.filter(Tag.value == tag).first()
    if tag_existing:
        return tag_existing
    else:
        return Tag.create(value=tag)


def get_tag_by_value(tag):
    return Tag.query.filter(Tag.value == tag).first()


def get_tags_by_names(tag_names):
    return Tag.query.filter(Tag.value.in_(tag_names)).all()


def are_all_tags_has_correct_length(tags):
    for tag in tags:
        if not (0 < len(tag.strip()) < int(current_app.config.get('INI_CONFIG', {}).get('max_tag_length'))):
            return False
    return True


def are_all_tags_has_valid_strings(tags):
    for tag in tags:
        if not valid_string_parser(tag):
            return False
    return True