from polylogyx.models import db, CarveSession, Node, CarvedBlock
from sqlalchemy import or_, and_, cast, desc
import sqlalchemy
from polylogyx.constants import ModelStatusFilters

def get_carves_by_node_id(node_id, searchterm=''):
    return db.session.query(CarveSession).filter(CarveSession.node_id == node_id).filter(ModelStatusFilters.HOSTS_NON_DELETED) \
        .filter(or_(
        Node.node_info['display_name'].astext.ilike('%' + searchterm + '%'),
        Node.node_info['computer_name'].astext.ilike('%' + searchterm + '%'),
        Node.node_info['hostname'].astext.ilike('%' + searchterm + '%'),
        CarveSession.session_id.ilike('%' + searchterm + '%'),
        CarveSession.archive.ilike('%' + searchterm + '%'),
        CarveSession.status.ilike('%' + searchterm + '%'),
        cast(CarveSession.created_at, sqlalchemy.String).ilike('%' + searchterm + '%'),
        cast(CarveSession.carve_size, sqlalchemy.String).ilike('%' + searchterm + '%'),
        cast(CarveSession.completed_blocks, sqlalchemy.String).ilike('%' + searchterm + '%')
    )).join(Node, CarveSession.node_id == Node.id).order_by(desc(CarveSession.id))


def get_carves_total_count(node_id=None):
    if node_id:
        return db.session.query(CarveSession).filter(CarveSession.node_id == node_id).filter(ModelStatusFilters.HOSTS_NON_DELETED).join(Node, CarveSession.node_id == Node.id).count()
    else:
        return db.session.query(CarveSession).filter(ModelStatusFilters.HOSTS_NON_DELETED).join(Node, CarveSession.node_id == Node.id).count()


def get_carves_all(searchterm='',column=None,order_by=None):
    if column == 'hostname':
        column=Node.node_info['computer_name']
    elif column == 'created_at':
        column = CarveSession.created_at
    if order_by and order_by in ['Asc','asc','ASC']:
        return db.session.query(CarveSession).filter(
            ModelStatusFilters.HOSTS_NON_DELETED).filter(or_(
            Node.node_info['display_name'].astext.ilike('%' + searchterm + '%'),
            Node.node_info['computer_name'].astext.ilike('%' + searchterm + '%'),
            Node.node_info['hostname'].astext.ilike('%' + searchterm + '%'),
            CarveSession.session_id.ilike('%' + searchterm + '%'),
            CarveSession.archive.ilike('%' + searchterm + '%'),
            CarveSession.status.ilike('%' + searchterm + '%'),
            cast(CarveSession.created_at, sqlalchemy.String).ilike('%' + searchterm + '%'),
            cast(CarveSession.carve_size, sqlalchemy.String).ilike('%' + searchterm + '%'),
            cast(CarveSession.completed_blocks, sqlalchemy.String).ilike('%' + searchterm + '%')
        )).join(Node, CarveSession.node_id == Node.id).group_by(CarveSession,Node).order_by(column)
    elif order_by and order_by in ['Desc','desc','DESC']:
        return db.session.query(CarveSession).filter(
            ModelStatusFilters.HOSTS_NON_DELETED).filter(or_(
            Node.node_info['display_name'].astext.ilike('%' + searchterm + '%'),
            Node.node_info['computer_name'].astext.ilike('%' + searchterm + '%'),
            Node.node_info['hostname'].astext.ilike('%' + searchterm + '%'),
            CarveSession.session_id.ilike('%' + searchterm + '%'),
            CarveSession.archive.ilike('%' + searchterm + '%'),
            CarveSession.status.ilike('%' + searchterm + '%'),
            cast(CarveSession.created_at, sqlalchemy.String).ilike('%' + searchterm + '%'),
            cast(CarveSession.carve_size, sqlalchemy.String).ilike('%' + searchterm + '%'),
            cast(CarveSession.completed_blocks, sqlalchemy.String).ilike('%' + searchterm + '%')
        )).join(Node, CarveSession.node_id == Node.id).group_by(Node,CarveSession).order_by(desc(column))
    else:
        return db.session.query(CarveSession).filter(ModelStatusFilters.HOSTS_NON_DELETED).filter(or_(
            Node.node_info['display_name'].astext.ilike('%' + searchterm + '%'),
            Node.node_info['computer_name'].astext.ilike('%' + searchterm + '%'),
            Node.node_info['hostname'].astext.ilike('%' + searchterm + '%'),
            CarveSession.session_id.ilike('%' + searchterm + '%'),
            CarveSession.archive.ilike('%' + searchterm + '%'),
            CarveSession.status.ilike('%' + searchterm + '%'),
            cast(CarveSession.created_at, sqlalchemy.String).ilike('%' + searchterm + '%'),
            cast(CarveSession.carve_size, sqlalchemy.String).ilike('%' + searchterm + '%'),
            cast(CarveSession.completed_blocks, sqlalchemy.String).ilike('%' + searchterm + '%')
        )).join(Node, CarveSession.node_id == Node.id).order_by(desc(CarveSession.id))


def get_carves_by_session_id(session_id):
    return CarveSession.query.filter(CarveSession.session_id == session_id).first()


def get_all_carves_by_session_ids(session_ids):
    return CarveSession.query.filter(CarveSession.session_id.in_(session_ids)).all()


def delete_carve(carve_session):
    return carve_session.delete()


def delete_carve_by_session_ids(session_ids):
    db.session.query(CarvedBlock).filter(CarvedBlock.session_id.in_(session_ids)).delete(synchronize_session=False)
    return db.session.query(CarveSession).filter(CarveSession.session_id.in_(session_ids)).delete(synchronize_session=False)