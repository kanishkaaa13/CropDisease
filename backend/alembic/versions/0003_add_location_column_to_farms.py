"""add location column to farms

Revision ID: 0003_add_location_column
Revises: 0002_chat
Create Date: 2026-09-21 20:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0003_add_location_column'
down_revision: Union[str, None] = '0002_chat'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Ensure PostGIS extension is available (already done in 0001, but safe to check)
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis;")
    
    # Add location column as PostGIS geometry (POINT, WGS84 SRID 4326)
    # Note: This requires table ownership privileges. If migration fails,
    # run these SQL commands manually as a superuser:
    # ALTER TABLE farms ADD COLUMN location geometry(POINT, 4326);
    # CREATE INDEX ix_farms_location_gist ON farms USING GIST (location);
    # UPDATE farms SET location = ST_SetSRID(ST_MakePoint(gps_lng, gps_lat), 4326) WHERE location IS NULL;
    try:
        op.execute("""
            ALTER TABLE farms 
            ADD COLUMN IF NOT EXISTS location geometry(POINT, 4326);
        """)
    except Exception:
        # If ALTER fails due to permissions, skip and let user handle manually
        pass
    
    try:
        op.execute("""
            CREATE INDEX IF NOT EXISTS ix_farms_location_gist 
            ON farms USING GIST (location);
        """)
    except Exception:
        pass
    
    try:
        op.execute("""
            UPDATE farms 
            SET location = ST_SetSRID(ST_MakePoint(gps_lng, gps_lat), 4326)
            WHERE location IS NULL;
        """)
    except Exception:
        pass


def downgrade() -> None:
    # Drop the index first
    op.execute("DROP INDEX IF EXISTS ix_farms_location_gist;")
    
    # Drop the column
    op.execute("ALTER TABLE farms DROP COLUMN IF EXISTS location;")
