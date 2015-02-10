"""Add subscribe column to user table

Revision ID: 4e435ff8ba74
Revises: bbba2255e00
Create Date: 2015-02-09 10:36:45.935116

"""

# revision identifiers, used by Alembic.
revision = '4e435ff8ba74'
down_revision = 'bbba2255e00'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('user', sa.Column('subscribed', sa.Boolean, default=True))
    query = 'UPDATE "user" SET subscribed=true;'
    op.execute(query)


def downgrade():
    op.drop_column('user', 'subscribed')
