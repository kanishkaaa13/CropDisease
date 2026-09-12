"""0001_initial_schema

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2026-09-13 01:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '0001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Ensure PostGIS extension is available
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis;")

    # 1. users
    op.create_table(
        'users',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('phone', sa.String(length=20), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('role', sa.String(length=50), nullable=False, server_default='farmer'),
        sa.Column('state', sa.String(length=100), nullable=True),
        sa.Column('district', sa.String(length=100), nullable=True),
        sa.Column('taluka', sa.String(length=100), nullable=True),
        sa.Column('village', sa.String(length=100), nullable=True),
        sa.Column('language_pref', sa.String(length=10), nullable=False, server_default='en'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('phone')
    )
    op.create_index('ix_users_phone', 'users', ['phone'])
    op.create_index('ix_users_role', 'users', ['role'])

    # 2. farms
    op.create_table(
        'farms',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('owner_id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('village', sa.String(length=150), nullable=False),
        sa.Column('taluka', sa.String(length=150), nullable=False),
        sa.Column('district', sa.String(length=150), nullable=False),
        sa.Column('state', sa.String(length=100), nullable=False),
        sa.Column('gps_lat', sa.Float(), nullable=False),
        sa.Column('gps_lng', sa.Float(), nullable=False),
        sa.Column('area_acres', sa.Float(), nullable=False),
        sa.Column('soil_type', sa.String(length=100), nullable=True),
        sa.Column('irrigation_type', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_farms_owner_id', 'farms', ['owner_id'])
    op.create_index('ix_farms_district', 'farms', ['district'])
    op.create_index('ix_farms_state', 'farms', ['state'])

    # 3. crops
    op.create_table(
        'crops',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('farm_id', sa.String(length=36), nullable=False),
        sa.Column('crop_name', sa.String(length=100), nullable=False),
        sa.Column('variety', sa.String(length=100), nullable=True),
        sa.Column('sowing_date', sa.Date(), nullable=True),
        sa.Column('growth_stage', sa.String(length=50), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='active'),
        sa.Column('expected_harvest_date', sa.Date(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['farm_id'], ['farms.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_crops_farm_id', 'crops', ['farm_id'])
    op.create_index('ix_crops_crop_name', 'crops', ['crop_name'])
    op.create_index('ix_crops_status', 'crops', ['status'])

    # 4. observations
    op.create_table(
        'observations',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('crop_id', sa.String(length=36), nullable=False),
        sa.Column('reported_by', sa.String(length=36), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('image_urls', sa.JSON(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('source', sa.String(length=50), nullable=False, server_default='scan'),
        sa.Column('gps_lat', sa.Float(), nullable=True),
        sa.Column('gps_lng', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['crop_id'], ['crops.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['reported_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_observations_crop_id', 'observations', ['crop_id'])
    op.create_index('ix_observations_reported_by', 'observations', ['reported_by'])
    op.create_index('ix_observations_timestamp', 'observations', ['timestamp'])

    # 5. ai_results
    op.create_table(
        'ai_results',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('observation_id', sa.String(length=36), nullable=False),
        sa.Column('disease_label', sa.String(length=150), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('severity_pct', sa.Float(), nullable=True),
        sa.Column('pest_label', sa.String(length=150), nullable=True),
        sa.Column('pest_confidence', sa.Float(), nullable=True),
        sa.Column('model_version', sa.String(length=50), nullable=False, server_default='v1.0.0'),
        sa.Column('heat_map_url', sa.String(length=500), nullable=True),
        sa.Column('treatment_recommendations', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['observation_id'], ['observations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('observation_id')
    )
    op.create_index('ix_ai_results_disease_label', 'ai_results', ['disease_label'])

    # 6. weather_snapshots
    op.create_table(
        'weather_snapshots',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('farm_id', sa.String(length=36), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('temp_c', sa.Float(), nullable=False),
        sa.Column('humidity_pct', sa.Float(), nullable=False),
        sa.Column('rainfall_mm', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('wind_speed_kmh', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('condition_text', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['farm_id'], ['farms.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_weather_snapshots_farm_id', 'weather_snapshots', ['farm_id'])
    op.create_index('ix_weather_snapshots_timestamp', 'weather_snapshots', ['timestamp'])
    op.create_index('ix_weather_snapshots_farm_timestamp', 'weather_snapshots', ['farm_id', 'timestamp'])

    # 7. risk_scores
    op.create_table(
        'risk_scores',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('crop_id', sa.String(length=36), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('disease_risk', sa.Float(), nullable=False),
        sa.Column('pest_risk', sa.Float(), nullable=False),
        sa.Column('weather_risk', sa.Float(), nullable=False),
        sa.Column('overall_score', sa.Float(), nullable=False),
        sa.Column('risk_level', sa.String(length=50), nullable=False),
        sa.Column('contributing_factors', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['crop_id'], ['crops.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_risk_scores_crop_id', 'risk_scores', ['crop_id'])
    op.create_index('ix_risk_scores_timestamp', 'risk_scores', ['timestamp'])
    op.create_index('ix_risk_scores_risk_level', 'risk_scores', ['risk_level'])

    # 8. alerts
    op.create_table(
        'alerts',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('crop_id', sa.String(length=36), nullable=False),
        sa.Column('risk_score_id', sa.String(length=36), nullable=True),
        sa.Column('level', sa.String(length=50), nullable=False, server_default='warning'),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('acknowledged', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('acknowledged_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('acknowledged_by', sa.String(length=36), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['acknowledged_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['crop_id'], ['crops.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['risk_score_id'], ['risk_scores.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_alerts_crop_id', 'alerts', ['crop_id'])
    op.create_index('ix_alerts_level', 'alerts', ['level'])
    op.create_index('ix_alerts_acknowledged', 'alerts', ['acknowledged'])

    # 9. expert_validations
    op.create_table(
        'expert_validations',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('ai_result_id', sa.String(length=36), nullable=False),
        sa.Column('officer_id', sa.String(length=36), nullable=False),
        sa.Column('verdict', sa.String(length=50), nullable=False),
        sa.Column('corrected_label', sa.String(length=150), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['ai_result_id'], ['ai_results.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['officer_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_expert_validations_ai_result_id', 'expert_validations', ['ai_result_id'])
    op.create_index('ix_expert_validations_officer_id', 'expert_validations', ['officer_id'])
    op.create_index('ix_expert_validations_verdict', 'expert_validations', ['verdict'])

    # 10. follow_ups
    op.create_table(
        'follow_ups',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('crop_id', sa.String(length=36), nullable=False),
        sa.Column('previous_observation_id', sa.String(length=36), nullable=False),
        sa.Column('new_observation_id', sa.String(length=36), nullable=False),
        sa.Column('severity_before', sa.Float(), nullable=False),
        sa.Column('severity_after', sa.Float(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['crop_id'], ['crops.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['new_observation_id'], ['observations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['previous_observation_id'], ['observations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_follow_ups_crop_id', 'follow_ups', ['crop_id'])
    op.create_index('ix_follow_ups_status', 'follow_ups', ['status'])

    # 11. pest_trap_readings
    op.create_table(
        'pest_trap_readings',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('farm_id', sa.String(length=36), nullable=False),
        sa.Column('trap_type', sa.String(length=100), nullable=False, server_default='Pheromone Trap'),
        sa.Column('location_description', sa.String(length=255), nullable=True),
        sa.Column('installed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_checked_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('image_url', sa.String(length=500), nullable=True),
        sa.Column('pest_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('dominant_pest', sa.String(length=150), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['farm_id'], ['farms.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_pest_trap_readings_farm_id', 'pest_trap_readings', ['farm_id'])
    op.create_index('ix_pest_trap_readings_last_checked_at', 'pest_trap_readings', ['last_checked_at'])
    op.create_index('ix_pest_trap_readings_farm_checked', 'pest_trap_readings', ['farm_id', 'last_checked_at'])


def downgrade() -> None:
    op.drop_table('pest_trap_readings')
    op.drop_table('follow_ups')
    op.drop_table('expert_validations')
    op.drop_table('alerts')
    op.drop_table('risk_scores')
    op.drop_table('weather_snapshots')
    op.drop_table('ai_results')
    op.drop_table('observations')
    op.drop_table('crops')
    op.drop_table('farms')
    op.drop_table('users')
