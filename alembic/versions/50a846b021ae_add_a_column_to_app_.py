"""Add a column to App for user access control

Revision ID: 50a846b021ae
Revises: 2a9a0ccb45fc
Create Date: 2013-03-21 12:21:44.199808

"""

# revision identifiers, used by Alembic.
revision = '50a846b021ae'
down_revision = '2a9a0ccb45fc'

from alembic import op
import sqlalchemy as sa


field = 'allow_anonymous_contributors'


def upgrade():
    op.add_column('app', sa.Column(field, sa.BOOLEAN, default=True))
    query = 'UPDATE app SET %s = True;' % field
    op.execute(query)


def downgrade():
    op.drop_column('app', field)
