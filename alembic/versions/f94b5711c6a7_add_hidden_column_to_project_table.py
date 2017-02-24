"""add hidden column to project table

Revision ID: f94b5711c6a7
Revises: 2bb53644b68b
Create Date: 2017-03-27 14:55:31.284942

"""

# revision identifiers, used by Alembic.
revision = 'f94b5711c6a7'
down_revision = '2bb53644b68b'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('project', sa.Column('hidden', sa.Boolean))


def downgrade():
    op.drop_column('project', 'hidden')
