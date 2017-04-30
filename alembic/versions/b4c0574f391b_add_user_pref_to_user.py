"""add user_pref to user

Revision ID: b4c0574f391b
Revises: 85d92b05ac78
Create Date: 2017-04-22 20:47:21.652220

"""

# revision identifiers, used by Alembic.
revision = 'b4c0574f391b'
down_revision = '85d92b05ac78'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

def upgrade():
    op.add_column('user', sa.Column('user_pref', JSONB))


def downgrade():
    op.drop_column('user', 'user_pref')
