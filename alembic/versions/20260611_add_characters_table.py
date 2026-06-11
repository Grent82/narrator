"""add characters table

Revision ID: 20260611
Revises: 532b1c8db9b3
Create Date: 2026-06-11

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20260611'
down_revision: Union[str, None] = '532b1c8db9b3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create characters table with Goal/Status/Motivation tracking."""
    op.create_table(
        'characters',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('story_id', sa.String(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('nickname', sa.String(length=255), nullable=True),
        sa.Column('is_player', sa.Boolean(), nullable=False, default=False),
        
        # Character profile data
        sa.Column('profile', sa.Text(), nullable=False, server_default=''),
        sa.Column('relation', sa.Text(), nullable=False, server_default=''),
        
        # Dynamic state (BookWorld-inspired)
        sa.Column('goal', sa.Text(), nullable=False, server_default=''),
        sa.Column('status', sa.Text(), nullable=False, server_default=''),
        sa.Column('motivation', sa.Text(), nullable=False, server_default=''),
        
        # Location tracking
        sa.Column('location_id', sa.String(), nullable=True),
        
        # Metadata
        sa.Column('activity', sa.Float(), nullable=False, default=1.0),
        sa.Column('metadata', sa.JSON(), nullable=False, server_default='{}'),
        
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['story_id'], ['stories.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['location_id'], ['locations.id'], ondelete='SET NULL'),
    )
    
    # Create index for faster lookups
    op.create_index('ix_characters_story_id', 'characters', ['story_id'])


def downgrade() -> None:
    """Drop characters table."""
    op.drop_index('ix_characters_story_id', table_name='characters')
    op.drop_table('characters')
