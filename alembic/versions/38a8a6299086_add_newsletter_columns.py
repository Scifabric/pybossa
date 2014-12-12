"""Add newsletter columns

Revision ID: 38a8a6299086
Revises: f8bc21a0be7
Create Date: 2014-12-10 10:29:17.619516

"""

# revision identifiers, used by Alembic.
revision = '38a8a6299086'
down_revision = 'f8bc21a0be7'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('user', sa.Column('newsletter_prompted', sa.Boolean, default=False))
    query = 'UPDATE "user" SET newsletter_prompted=false;'
    op.execute(query)


def downgrade():
    op.drop_column('user', 'newsletter_prompted')
