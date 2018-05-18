"""empty message for add user_pref to user

Revision ID: d317dc38cf39
Revises: fa8cf884aa8e
Create Date: 2018-02-13 22:24:18.363617

"""

# revision identifiers, used by Alembic.
revision = 'd317dc38cf39'
down_revision = 'fa8cf884aa8e'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

def upgrade():
    pass #op.add_column('user', sa.Column('user_pref', JSONB))


def downgrade():
    pass #op.drop_column('user', 'user_pref')
