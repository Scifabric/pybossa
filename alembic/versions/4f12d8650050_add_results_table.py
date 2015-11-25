"""add results table

Revision ID: 4f12d8650050
Revises: 4a571e217ab8
Create Date: 2015-11-23 10:55:00.909453

"""

# revision identifiers, used by Alembic.
revision = '4f12d8650050'
down_revision = '4a571e217ab8'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY, JSON
import datetime


def make_timestamp():
    now = datetime.datetime.utcnow()
    return now.isoformat()


def upgrade():
    op.create_table(
        'result',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('created', sa.Text, default=make_timestamp),
        sa.Column('project_id', sa.Integer, sa.ForeignKey('project.id'), nullable=False),
        sa.Column('task_id', sa.Integer, sa.ForeignKey('task.id'), nullable=False),
        sa.Column('task_run_ids', ARRAY(sa.Integer), nullable=False),
        sa.Column('last_version', sa.Boolean, default=True),
        sa.Column('info', JSON)
    )


def downgrade():
    op.drop_table('result')
