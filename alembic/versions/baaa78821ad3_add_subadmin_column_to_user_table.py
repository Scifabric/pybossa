"""added subadmin field

Revision ID: baaa78821ad3
Revises: 8ce9b3da799e
Create Date: 2017-02-01 18:18:24.496622

"""

# revision identifiers, used by Alembic.
revision = 'baaa78821ad3'
down_revision = '8ce9b3da799e'

from alembic import op
import sqlalchemy as sa

def upgrade():
    op.add_column('user', sa.Column('subadmin', sa.Boolean, default=False))
    query = 'UPDATE "user" SET subadmin=false;'
    op.execute(query)

def downgrade():
    op.drop_column('user', 'subadmin')
