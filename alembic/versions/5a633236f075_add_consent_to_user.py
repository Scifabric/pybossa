"""add consent to user

Revision ID: 5a633236f075
Revises: 4e795a38cd4b
Create Date: 2017-08-22 10:20:40.064646

"""

# revision identifiers, used by Alembic.
revision = '5a633236f075'
down_revision = '4e795a38cd4b'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('user', sa.Column('consent', sa.Boolean, default=False))
    query = 'UPDATE "user" SET consent=false'
    op.execute(query)


def downgrade():
    op.drop_column('user', 'consent')
