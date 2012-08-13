"""big int for oauth id

Revision ID: 25e478de8a63
Revises: 51d3131cf450
Create Date: 2012-08-13 13:46:01.748992

"""

# revision identifiers, used by Alembic.
revision = '25e478de8a63'
down_revision = '51d3131cf450'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.alter_column('user', 'facebook_user_id', type_=sa.BigInteger)
    op.alter_column('user', 'twitter_user_id', type_=sa.BigInteger)


def downgrade():
    op.alter_column('user', 'facebook_user_id', type_=sa.Integer)
    op.alter_column('user', 'twitter_user_id', type_=sa.Integer)
