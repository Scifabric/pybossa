"""add user_pref to task

Revision ID: fdb3e513b13b
Revises: b4c0574f391b
Create Date: 2017-04-22 20:47:43.660870

"""

# revision identifiers, used by Alembic.
revision = 'fdb3e513b13b'
down_revision = 'b4c0574f391b'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

def upgrade():
    op.add_column('task', sa.Column('user_pref', JSONB))


def downgrade():
    op.drop_column('task', 'user_pref')
