"""add_parent_location_id_to_locations

Revision ID: a8cfea92f3f5
Revises: 20260611_03
Create Date: 2026-06-12 16:04:30.029415
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a8cfea92f3f5'
down_revision = '20260611_03'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('locations', sa.Column('parent_location_id', sa.String(), nullable=True))
    op.create_foreign_key(
        'fk_locations_parent_location',
        'locations', 'locations',
        ['parent_location_id'], ['id'],
        ondelete='SET NULL'
    )


def downgrade() -> None:
    op.drop_constraint('fk_locations_parent_location', 'locations', type_='foreignkey')
    op.drop_column('locations', 'parent_location_id')
