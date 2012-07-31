"""admin field for users

Revision ID: 25c325f4e749
Revises: 10720fc1bdcd
Create Date: 2012-07-31 11:11:17.151503

"""

# revision identifiers, used by Alembic.
revision = '25c325f4e749'
down_revision = '10720fc1bdcd'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('user', sa.Column('admin', sa.Integer))


def downgrade():
    op.drop_column('user', 'admin')
