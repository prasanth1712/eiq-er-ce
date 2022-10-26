"""empty message

Revision ID: 90988dd06a28
Revises: 32313bfdafab
Create Date: 2022-06-09 15:03:12.580278

"""

# revision identifiers, used by Alembic.
revision = '90988dd06a28'
down_revision = '32313bfdafab'

from alembic import op
import sqlalchemy as sa
import polylogyx.db.database
import flask_authorize



def upgrade():

    op.execute("drop view if exists  result_log_view")
    op.execute("drop sequence if exists  result_log_id_seq1")
    op.execute("drop function if exists  createPartitionIfNotExists")

    op.execute("alter table IF EXISTS result_log alter column id type bigint")
    op.execute("alter table IF EXISTS result_log_maps alter column result_log_id type bigint")
    op.execute("alter table IF EXISTS result_log_maps alter column result_log_scan_id type bigint")
    op.execute("alter table IF EXISTS result_log_scan alter column id type bigint")
    op.execute("alter table IF EXISTS status_log alter column id type bigint")
    op.execute("alter table IF EXISTS alerts alter column id type bigint")
    op.execute("alter table IF EXISTS alert_log alter column id type bigint")
    op.execute("alter sequence if exists result_log_seq as bigint cycle")
    op.execute("alter sequence if exists result_log_scan_id_seq as bigint cycle")
    op.execute("alter sequence if exists status_log_id_seq as bigint cycle")
    op.execute("alter sequence if exists alerts_id_seq as bigint cycle")
    op.execute("alter sequence if exists alert_log_id_seq as bigint cycle")


def downgrade():
    pass
    # op.execute("alter table IF EXISTS result_log alter column id type integer")
    # op.execute("alter table IF EXISTS result_log_maps alter column result_log_id type integer")
    # op.execute("alter table IF EXISTS result_log_maps alter column result_log_scan_id type integer")
    # op.execute("alter table IF EXISTS result_log_scan alter column id type integer")
    # op.execute("alter table IF EXISTS status_log alter column id type integer")
    # op.execute("alter table IF EXISTS alerts alter column id type integer")
    # op.execute("alter table IF EXISTS alert_log alter column id type integer")
    # op.execute("alter sequence if exists result_log_seq as integer no cycle")
    # op.execute("alter sequence if exists result_log_scan_id_seq as integer no cycle")
    # op.execute("alter sequence if exists status_log_id_seq as integer no cycle")
    # op.execute("alter sequence if exists alerts_id_seq as integer no cycle")
    # op.execute("alter sequence if exists alert_log_id_seq as integer no cycle")
