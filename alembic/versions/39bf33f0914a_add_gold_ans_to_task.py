"""add gold_ans to task

Revision ID: 39bf33f0914a
Revises: 2edf951cc6ae
Create Date: 2018-10-19 11:49:28.978267

"""

# revision identifiers, used by Alembic.
revision = '39bf33f0914a'
down_revision = '2edf951cc6ae'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

def upgrade():
    op.add_column('task', sa.Column('gold_answers', JSONB))


def downgrade():
    op.drop_column('task', 'gold_answers')
