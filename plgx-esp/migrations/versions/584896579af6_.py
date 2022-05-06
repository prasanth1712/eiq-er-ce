"""empty message

Revision ID: 584896579af6
Revises: 233d98c00d66
Create Date: 2019-02-07 18:11:20.194413

"""

# revision identifiers, used by Alembic.
revision = "584896579af6"
down_revision = "f04a79a898c2"
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


def upgrade():
    op.create_table(
        "result_log_scan",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("scan_type", sa.String(), nullable=False),
        sa.Column("scan_value", sa.String(), nullable=True),
        sa.Column("reputations", postgresql.JSONB(), default={}, nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "manual_threat_intel",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("value", sa.String(), nullable=True),
        sa.Column("threat_name", sa.String(), nullable=True),
        sa.Column("intel_type", sa.String(), nullable=False),
        sa.Column("severity", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade():
    op.drop_table("result_log_scan")
    op.drop_table("manual_threat_intel")
