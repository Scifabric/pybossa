"""create featured field for app

Revision ID: 10720fc1bdcd
Revises: a0d7c1872e
Create Date: 2012-07-31 11:08:44.728339

"""

# revision identifiers, used by Alembic.
revision = '10720fc1bdcd'
down_revision = 'a0d7c1872e'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('app', sa.Column('featured', sa.Integer))


def downgrade():
    op.drop_column('app', 'featured')
