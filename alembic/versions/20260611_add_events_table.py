"""add events table for intervention/event system

Revision ID: 20260611_03
Revises: 20260611_02
Create Date: 2026-06-11

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20260611_03'
down_revision: Union[str, None] = '20260611_02'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create events table for global events and interventions."""
    op.create_table(
        'events',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('story_id', sa.String(), nullable=False),
        sa.Column('event_type', sa.String(50), nullable=False, server_default='global_event'),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False, server_default=''),
        sa.Column('intervention', sa.Text(), nullable=False, server_default=''),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('priority', sa.Integer(), nullable=False, default=0),
        sa.Column('location_id', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('ended_at', sa.DateTime(), nullable=True),
        
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['story_id'], ['stories.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['location_id'], ['locations.id'], ondelete='SET NULL'),
    )
    
    # Create indexes
    op.create_index('ix_events_story_id', 'events', ['story_id'])
    op.create_index('ix_events_active', 'events', ['is_active'])
    op.create_index('ix_events_priority', 'events', ['priority'])


def downgrade() -> None:
    """Drop events table."""
    op.drop_index('ix_events_priority', table_name='events')
    op.drop_index('ix_events_active', table_name='events')
    op.drop_index('ix_events_story_id', table_name='events')
    op.drop_table('events')
