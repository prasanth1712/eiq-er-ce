"""empty message

Revision ID: d39e8fda100e
Revises: 2eea3c907781
Create Date: 2022-02-17 16:09:45.088741

"""

# revision identifiers, used by Alembic.
revision = 'd39e8fda100e'
down_revision = '2eea3c907781'

from alembic import op
import sqlalchemy as sa
import polylogyx.db.database
import flask_authorize



def upgrade():
    op.execute(
        "CREATE INDEX IF NOT EXISTS IDX_IOC_INTEL_TYPE ON IOC_INTEL (TYPE);"
    )

    op.execute(
        "CREATE INDEX IF NOT EXISTS IDX_IOC_INTEL_VALUE ON IOC_INTEL (LOWER(VALUE));"
    )


def downgrade():
    op.execute(
        "DROP INDEX IF EXISTS IDX_IOC_INTEL_TYPE;"
    )
    op.execute(
        "DROP INDEX IF EXISTS IDX_IOC_INTEL_VALUE;"
    )
