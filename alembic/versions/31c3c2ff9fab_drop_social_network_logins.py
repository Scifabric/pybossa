"""drop social network logins

Revision ID: 31c3c2ff9fab
Revises: a791f9de9ac3
Create Date: 2021-02-27 10:17:17.122501

"""

# revision identifiers, used by Alembic.
revision = '31c3c2ff9fab'
down_revision = 'a791f9de9ac3'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.drop_column('user', 'twitter_user_id')
    op.drop_column('user', 'google_user_id')
    op.drop_column('user', 'facebook_user_id')


def downgrade():
    op.add_column('user', sa.Column('twitter_user_id', sa.BigInteger, unique=True))
    op.add_column('user', sa.Column('google_user_id', sa.BigInteger, unique=True))
    op.add_column('user', sa.Column('facebook_user_id', sa.BigInteger, unique=True))
