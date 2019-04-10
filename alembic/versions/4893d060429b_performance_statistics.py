"""performance statistics

Revision ID: 4893d060429b
Revises: 7b5f75fc2c08
Create Date: 2019-03-16 15:40:25.595553

"""

# revision identifiers, used by Alembic.
revision = '4893d060429b'
down_revision = '7b5f75fc2c08'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, ENUM
import datetime


def upgrade():
    op.create_table(
        'performance_stats',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('project_id', sa.Integer, sa.ForeignKey('project.id', ondelete='CASCADE'), nullable=False),
        sa.Column('field', sa.Text, nullable=False),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('user.id'), nullable=False),
        sa.Column('user_key', sa.Text),
        sa.Column('stat_type', ENUM(name='statistic', create_type=False), nullable=False),
        sa.Column('info', JSONB)
    )


def downgrade():
    op.drop_table('performance_stats')
