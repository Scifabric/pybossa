"""add google user id

Revision ID: 2a9a0ccb45fc
Revises: 4f04ded45835
Create Date: 2012-10-08 13:10:20.994389

"""

# revision identifiers, used by Alembic.
revision = '2a9a0ccb45fc'
down_revision = '4f04ded45835'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('user', sa.Column('google_user_id', sa.String, unique=True))


def downgrade():
    op.drop_column('user', 'google_user_id')
