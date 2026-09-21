"""Add indexes for officer map queries

Revision ID: 0005
Revises: 0004
Create Date: 2026-09-21

"""
from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade():
    op.create_index("ix_farms_district_state", "farms", ["district", "state"], unique=False)
    op.create_index("ix_observations_timestamp", "observations", ["timestamp"], unique=False)


def downgrade():
    op.drop_index("ix_observations_timestamp", table_name="observations")
    op.drop_index("ix_farms_district_state", table_name="farms")
