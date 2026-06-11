"""add location connections table

Revision ID: 20260611_02
Revises: 20260611
Create Date: 2026-06-11

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20260611_02'
down_revision: Union[str, None] = '20260611'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create location_connections table for distance network."""
    op.create_table(
        'location_connections',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('story_id', sa.String(), nullable=False),
        sa.Column('from_location_id', sa.String(), nullable=False),
        sa.Column('to_location_id', sa.String(), nullable=False),
        sa.Column('distance', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('travel_time_hours', sa.Float(), nullable=True),
        sa.Column('difficulty', sa.String(50), nullable=False, server_default='normal'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['story_id'], ['stories.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['from_location_id'], ['locations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['to_location_id'], ['locations.id'], ondelete='CASCADE'),
    )
    
    # Create indexes for faster lookups
    op.create_index('ix_location_connections_story_id', 'location_connections', ['story_id'])
    op.create_index('ix_location_connections_from_location', 'location_connections', ['from_location_id'])
    op.create_index('ix_location_connections_to_location', 'location_connections', ['to_location_id'])
    
    # Create unique constraint to prevent duplicate connections
    op.create_unique_constraint(
        'uq_location_connections',
        'location_connections',
        ['story_id', 'from_location_id', 'to_location_id']
    )


def downgrade() -> None:
    """Drop location_connections table."""
    op.drop_constraint('uq_location_connections', 'location_connections', type_='unique')
    op.drop_index('ix_location_connections_to_location', table_name='location_connections')
    op.drop_index('ix_location_connections_from_location', table_name='location_connections')
    op.drop_index('ix_location_connections_story_id', table_name='location_connections')
    op.drop_table('location_connections')
