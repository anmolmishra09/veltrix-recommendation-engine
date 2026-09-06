"""Initial schema creation

Revision ID: 001_initial_schema
Revises:
Create Date: 2026-09-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('external_id', sa.String(length=255), nullable=False),
        sa.Column('age', sa.Integer(), nullable=True),
        sa.Column('gender', sa.String(length=50), nullable=True),
        sa.Column('location', sa.String(length=255), nullable=True),
        sa.Column('registration_timestamp', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_users_external_id', 'users', ['external_id'], unique=False)
    op.create_index('idx_users_location', 'users', ['location'], unique=False)
    op.create_index('idx_users_registration', 'users', ['registration_timestamp'], unique=False)

    # Create products table
    op.create_table(
        'products',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('subcategory', sa.String(length=100), nullable=True),
        sa.Column('price', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('brand', sa.String(length=100), nullable=True),
        sa.Column('inventory', sa.Integer(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_products_category', 'products', ['category'], unique=False)
    op.create_index('idx_products_subcategory', 'products', ['subcategory'], unique=False)
    op.create_index('idx_products_price', 'products', ['price'], unique=False)
    op.create_index('idx_products_brand', 'products', ['brand'], unique=False)
    op.create_index('idx_products_inventory', 'products', ['inventory'], unique=False)

    # Create interactions table
    op.create_table(
        'interactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('event_type', sa.String(length=50), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('session_id', sa.String(length=255), nullable=True),
        sa.Column('context', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('recommendation_id', sa.Integer(), nullable=True),
        sa.Column('ranking_position', sa.Integer(), nullable=True),
        sa.Column('recommendation_score', sa.Numeric(precision=5, scale=4), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_interactions_user_id', 'interactions', ['user_id'], unique=False)
    op.create_index('idx_interactions_product_id', 'interactions', ['product_id'], unique=False)
    op.create_index('idx_interactions_event_type', 'interactions', ['event_type'], unique=False)
    op.create_index('idx_interactions_timestamp', 'interactions', ['timestamp'], unique=False)
    op.create_index('idx_interactions_session_id', 'interactions', ['session_id'], unique=False)
    op.create_index('idx_interactions_user_product', 'interactions', ['user_id', 'product_id'], unique=False)
    op.create_index('idx_interactions_user_event', 'interactions', ['user_id', 'event_type'], unique=False)
    op.create_index('idx_interactions_product_event', 'interactions', ['product_id', 'event_type'], unique=False)
    op.create_foreign_key(None, 'interactions', 'users', ['user_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key(None, 'interactions', 'products', ['product_id'], ['id'], ondelete='CASCADE')

    # Create recommendations table
    op.create_table(
        'recommendations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('context', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('model_version', sa.String(length=100), nullable=True),
        sa.Column('experiment_id', sa.String(length=100), nullable=True),
        sa.Column('num_candidates', sa.Integer(), nullable=True),
        sa.Column('num_returned', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_recommendations_user_id', 'recommendations', ['user_id'], unique=False)
    op.create_index('idx_recommendations_created_at', 'recommendations', ['created_at'], unique=False)
    op.create_index('idx_recommendations_model_version', 'recommendations', ['model_version'], unique=False)
    op.create_index('idx_recommendations_experiment_id', 'recommendations', ['experiment_id'], unique=False)
    op.create_foreign_key(None, 'recommendations', 'users', ['user_id'], ['id'], ondelete='CASCADE')

    # Create experiments table
    op.create_table(
        'experiments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('experiment_id', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('start_timestamp', sa.DateTime(timezone=True), nullable=True),
        sa.Column('end_timestamp', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('config', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('experiment_id')
    )
    op.create_index('idx_experiments_status', 'experiments', ['status'], unique=False)
    op.create_index('idx_experiments_start', 'experiments', ['start_timestamp'], unique=False)
    op.create_index('idx_experiments_end', 'experiments', ['end_timestamp'], unique=False)

    # Create experiment_assignments table
    op.create_table(
        'experiment_assignments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('experiment_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('variant', sa.String(length=50), nullable=False),
        sa.Column('model_version', sa.String(length=100), nullable=True),
        sa.Column('assigned_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_experiment_assignments_experiment', 'experiment_assignments', ['experiment_id'], unique=False)
    op.create_index('idx_experiment_assignments_user', 'experiment_assignments', ['user_id'], unique=False)
    op.create_index('idx_experiment_assignments_variant', 'experiment_assignments', ['variant'], unique=False)
    op.create_foreign_key(None, 'experiment_assignments', 'experiments', ['experiment_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key(None, 'experiment_assignments', 'users', ['user_id'], ['id'], ondelete='CASCADE')
    op.create_unique_constraint(None, 'experiment_assignments', ['experiment_id', 'user_id'])


def downgrade():
    # Drop tables in reverse order to avoid foreign key constraints
    op.drop_table('experiment_assignments')
    op.drop_table('experiments')
    op.drop_table('recommendations')
    op.drop_table('interactions')
    op.drop_table('products')
    op.drop_table('users')