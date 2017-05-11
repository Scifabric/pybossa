"""table_task_taskrun_counts

Revision ID: 920578f0de9c
Revises: 9a83475c60c3
Create Date: 2017-05-11 14:32:43.731109

"""

# revision identifiers, used by Alembic.
revision = '920578f0de9c'
down_revision = '9a83475c60c3'

from alembic import op
from sqlalchemy.dialects.postgresql import TIMESTAMP
import sqlalchemy as sa


def upgrade():
    op.create_table('counter',
                    sa.Column('id', sa.Integer, primary_key=True),
                    sa.Column('created', TIMESTAMP),
                    sa.Column('project_id', sa.Integer, 
                              sa.ForeignKey('project.id',
                                            ondelete='CASCADE'),
                              nullable=False),
                    sa.Column('task_id', sa.Integer,
                              sa.ForeignKey('task.id',
                                            ondelete='CASCADE'),
                              nullable=False),
                    sa.Column('n_task_runs', sa.Integer,
                              default=0, nullable=False),
                    )


def downgrade():
    op.drop_table('counter')
