"""projects_stats

Revision ID: d1add5e3e65e
Revises: ca9164362ca2
Create Date: 2017-06-16 14:03:24.978654

"""

# revision identifiers, used by Alembic.
revision = 'd1add5e3e65e'
down_revision = 'ca9164362ca2'

from sqlalchemy.dialects.postgresql import JSON
from alembic import op
import sqlalchemy as sa

def make_timestamp():
    now = datetime.datetime.utcnow()
    return now.isoformat()


def upgrade():
    op.create_table(
        'project_stats',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('project_id', sa.Integer, sa.ForeignKey('project.id',
                                                          ondelete='CASCADE')),
        sa.Column('n_tasks', sa.Integer, default=0),
        sa.Column('n_task_runs', sa.Integer, default=0),
        sa.Column('n_results', sa.Integer, default=0),
        sa.Column('n_volunteers', sa.Integer, default=0),
        sa.Column('n_completed_tasks', sa.Integer, default=0),
        sa.Column('overall_progress', sa.Integer, default=0),
        sa.Column('average_time', sa.Float, default=0),
        sa.Column('n_blogposts', sa.Integer, default=0),
        sa.Column('last_activity', sa.Text, default=make_timestamp),
        sa.Column('info', JSON, nullable=False)
    )


def downgrade():
    op.drop_table('project_stats')
