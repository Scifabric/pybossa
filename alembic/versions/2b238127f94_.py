"""Add task_runs_nr column to task

Revision ID: 2b238127f94
Revises: 3620d7cac37b
Create Date: 2014-03-12 16:09:34.142841

"""

# revision identifiers, used by Alembic.
revision = '2b238127f94'
down_revision = '3620d7cac37b'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('task', sa.Column('task_runs_nr', sa.Integer(), nullable=True, server_default='0'))


def downgrade():
    op.drop_column('task', 'task_runs_nr')
