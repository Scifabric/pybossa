"""add discourse_comment table

Revision ID: ace3254a03b5
Revises: d42631c07887
Create Date: 2016-09-02 07:19:45.119454

"""

# revision identifiers, used by Alembic.
revision = 'ace3254a03b5'
down_revision = 'd42631c07887'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table(
    'discourse_comment',
    sa.Column('task_id', sa.Integer, sa.ForeignKey('task.id', ondelete='CASCADE'), primary_key=True, nullable=False),
    sa.Column('discourse_topic_id', sa.Integer)
    )


def downgrade():
    op.drop_table('discourse_comment')