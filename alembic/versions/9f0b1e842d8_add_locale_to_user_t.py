"""add locale to user table

Revision ID: 9f0b1e842d8
Revises: 50a846b021ae
Create Date: 2013-03-26 13:55:36.669733

"""

# revision identifiers, used by Alembic.
revision = '9f0b1e842d8'
down_revision = '50a846b021ae'

from alembic import op
import sqlalchemy as sa


field = 'locale'


def upgrade():
    op.add_column('user', sa.Column(field, sa.String, default="en"))
    query = 'UPDATE "user" SET %s=\'en\';' % field
    op.execute(query)


def downgrade():
    op.drop_column('user', field)
