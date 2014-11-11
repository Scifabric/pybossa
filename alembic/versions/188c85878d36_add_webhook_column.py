"""add webhook column

Revision ID: 188c85878d36
Revises: a9ecd1c767
Create Date: 2014-11-06 11:06:28.337421

"""

# revision identifiers, used by Alembic.
revision = '188c85878d36'
down_revision = 'a9ecd1c767'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('app', sa.Column('webhook', sa.Text))


def downgrade():
    op.drop_column('app', 'webhook')
