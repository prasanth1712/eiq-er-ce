"""empty message

Revision ID: cfc2591fe64b
Revises: 95a0deb3919d
Create Date: 2022-08-19 12:05:03.633252

"""

# revision identifiers, used by Alembic.
revision = 'cfc2591fe64b'
down_revision = '95a0deb3919d'

from alembic import op
import sqlalchemy as sa
import polylogyx.db.database
from sqlalchemy import orm
import flask_authorize



def upgrade():
    # assign configs to nodes
    bind = op.get_bind()
    session = orm.Session(bind=bind)

    triggers = session.execute("select trigger_name,event_object_table from information_schema.triggers where trigger_name like 'node_query_count_%';")
    for trigger in triggers:
        qry = f'DROP TRIGGER IF EXISTS {trigger[0]} ON {trigger[1]} CASCADE;'
        res = session.execute(qry)

    trigger_funcs = session.execute("select routine_name from information_schema.routines where routine_name like 'node_query_count%';")
    for trigger_func in trigger_funcs:
        qry = f'DROP FUNCTION  IF EXISTS  {trigger_func[0]} CASCADE;'
        res = session.execute(qry)
        
    session.commit()
    # ### end Alembic commands ###


def downgrade():
    pass
