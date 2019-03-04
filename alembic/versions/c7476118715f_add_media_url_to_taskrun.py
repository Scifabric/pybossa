"""Add media_url to TaskRun

Revision ID: c7476118715f
Revises: 174eb928136a
Create Date: 2018-08-22 11:36:32.851149

"""

# revision identifiers, used by Alembic.
revision = 'c7476118715f'
down_revision = '174eb928136a'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('task_run', sa.Column('media_url', sa.String))


def downgrade():
    op.drop_column('task_run', 'media_url')
