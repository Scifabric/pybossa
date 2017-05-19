"""add_fk_indices

Revision ID: 25927be2b965
Revises: fdb3e513b13b
Create Date: 2017-05-18 10:17:12.114940

"""

# revision identifiers, used by Alembic.
revision = '25927be2b965'
down_revision = 'fdb3e513b13b'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_index('task_run_user_id_idx', 'task_run', ['user_id'])
    op.create_index('task_run_project_id_idx', 'task_run', ['project_id'])
    op.create_index('project_owner_id_idx', 'project', ['owner_id'])
    op.create_index('result_project_id_idx', 'result', ['project_id'])
    op.create_index('result_task_id_idx', 'result', ['task_id'])


def downgrade():
    op.drop_index('task_run_user_id_idx')
    op.drop_index('task_run_project_id_idx')
    op.drop_index('project_owner_id_idx')
    op.drop_index('result_project_id_idx')
    op.drop_index('result_task_id_idx')
