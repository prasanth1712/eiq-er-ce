from polylogyx.models import db, CarveSession, Node
from sqlalchemy import or_, and_, cast, desc
import sqlalchemy


def get_carves_by_node_id(node_id, searchterm=''):
    return db.session.query(CarveSession).filter(CarveSession.node_id == node_id).filter(and_(Node.state!=Node.REMOVED, Node.state!=Node.DELETED)) \
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
        return db.session.query(CarveSession).filter(CarveSession.node_id == node_id).filter(and_(Node.state!=Node.REMOVED, Node.state!=Node.DELETED)).join(Node, CarveSession.node_id == Node.id).count()
    else:
        return db.session.query(CarveSession).filter(and_(Node.state!=Node.REMOVED, Node.state!=Node.DELETED)).join(Node, CarveSession.node_id == Node.id).count()


def get_carves_all(searchterm=''):
    return db.session.query(CarveSession).filter(and_(Node.state!=Node.REMOVED, Node.state!=Node.DELETED)).filter(or_(
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


def delete_carve(carve_session):
    return carve_session.delete()
