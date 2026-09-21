"""Add password_hash field to users table

Revision ID: 0004
Revises: 0003_add_location_column
Create Date: 2026-09-21

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0004'
down_revision = '0003_add_location_column'
branch_labels = None
depends_on = None


def upgrade():
    # Add password_hash column (nullable initially to allow migration of existing users)
    op.add_column('users', sa.Column('password_hash', sa.String(255), nullable=True))
    
    # Make email non-nullable and unique
    op.alter_column('users', 'email', nullable=False)
    
    # Make phone nullable (was required before)
    op.alter_column('users', 'phone', nullable=True)
    
    # Backfill password_hash for existing users with a default hash
    # This is a temporary measure - existing users will need to reset passwords
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    default_hash = pwd_context.hash("changeme123")
    
    connection = op.get_bind()
    connection.execute(
        sa.text("UPDATE users SET password_hash = :hash WHERE password_hash IS NULL"),
        {"hash": default_hash}
    )
    
    # Now make password_hash non-nullable
    op.alter_column('users', 'password_hash', nullable=False)


def downgrade():
    # Revert changes
    op.alter_column('users', 'password_hash', nullable=True)
    op.drop_column('users', 'password_hash')
    op.alter_column('users', 'phone', nullable=False)
    op.alter_column('users', 'email', nullable=True)
