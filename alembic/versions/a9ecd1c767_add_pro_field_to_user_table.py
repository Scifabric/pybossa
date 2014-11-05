"""add pro field to user table

Revision ID: a9ecd1c767
Revises: 66594a9866c
Create Date: 2014-11-05 10:31:37.734790

"""

# revision identifiers, used by Alembic.
revision = 'a9ecd1c767'
down_revision = '66594a9866c'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('user', sa.Column('pro', sa.Boolean, default=False))
    query = 'UPDATE "user" SET pro=false;'
    op.execute(query)


def downgrade():
    op.drop_column('user', 'pro')
