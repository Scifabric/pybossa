"""add index on task info

Revision ID: 2bb53644b68b
Revises: 216fdf24c4e0
Create Date: 2017-03-21 11:31:12.397176

"""

# revision identifiers, used by Alembic.
revision = '2bb53644b68b'
down_revision = 'baaa78821ad3'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_index('task_info_idx', 'task', [sa.text('md5(info::text)')])


def downgrade():
    op.drop_index('task_info_idx')
