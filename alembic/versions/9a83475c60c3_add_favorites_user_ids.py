"""Add favorites user_ids

Revision ID: 9a83475c60c3
Revises: 8ce9b3da799e
Create Date: 2017-03-28 11:37:03.861572

"""

# revision identifiers, used by Alembic.
revision = '9a83475c60c3'
down_revision = '8ce9b3da799e'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

field = 'fav_user_ids'

def upgrade():
    op.add_column('task', sa.Column(field, postgresql.ARRAY(sa.Integer)))


def downgrade():
    op.drop_column('task', field)
