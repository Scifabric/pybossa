"""add privacy mode to user

Revision ID: 4ad4fddc76f8
Revises: 3620d7cac37b
Create Date: 2014-02-26 16:48:19.575577

"""

# revision identifiers, used by Alembic.
revision = '4ad4fddc76f8'
down_revision = '3620d7cac37b'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('user', sa.Column('privacy_mode', sa.Boolean, default=True))
    query = 'UPDATE "user" SET privacy_mode=true;'
    op.execute(query)



def downgrade():
    op.drop_column('user', 'privacy_mode')
