"""admin field for users

Revision ID: 9341dfd1b21
Revises: a0d7c1872e
Create Date: 2012-07-31 17:12:24.229677

"""

# revision identifiers, used by Alembic.
revision = '9341dfd1b21'
down_revision = 'a0d7c1872e'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('user', sa.Column('admin', sa.Boolean, default=False))


def downgrade():
    op.drop_column('user', 'admin')
