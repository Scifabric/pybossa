"""create indexes on task and taskrun

Revision ID: 263677aea8ab
Revises: f94b5711c6a7
Create Date: 2017-03-27 17:14:22.948537

"""

# revision identifiers, used by Alembic.
revision = '263677aea8ab'
down_revision = 'f94b5711c6a7'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_index('task_run_task_id_idx', 'task_run', ['task_id'])
    op.create_index('task_project_id_idx', 'task', ['project_id'])


def downgrade():
    op.drop_index('task_project_id_idx')
    op.drop_index('task_run_task_id_idx')
