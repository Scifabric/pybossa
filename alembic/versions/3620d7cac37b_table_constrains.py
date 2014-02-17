"""table_constrains

Revision ID: 3620d7cac37b
Revises: 3f113ca6c186
Create Date: 2014-01-09 13:20:30.954637

"""

# revision identifiers, used by Alembic.
revision = '3620d7cac37b'
down_revision = '3f113ca6c186'

from alembic import op
import sqlalchemy as sa


def upgrade():
    # App table
    op.alter_column('app', 'name', nullable=False)
    op.alter_column('app', 'short_name', nullable=False)
    op.alter_column('app', 'description', nullable=False)
    op.alter_column('app', 'owner_id', nullable=False)
    # Task
    op.alter_column('task', 'app_id', nullable=False)

    # TaskRun
    op.alter_column('task_run', 'app_id', nullable=False)
    op.alter_column('task_run', 'task_id', nullable=False)


def downgrade():
    op.alter_column('app', 'name', nullable=True)
    op.alter_column('app', 'short_name', nullable=True)
    op.alter_column('app', 'description', nullable=True)
    op.alter_column('app', 'owner_id', nullable=True)
    # Task
    op.alter_column('task', 'app_id', nullable=True)

    # TaskRun
    op.alter_column('task_run', 'app_id', nullable=True)
    op.alter_column('task_run', 'task_id', nullable=True)
