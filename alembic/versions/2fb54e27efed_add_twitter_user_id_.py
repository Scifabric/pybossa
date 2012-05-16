"""Add twitter_user_id to the Column:User

Revision ID: 2fb54e27efed
Revises: None
Create Date: 2012-05-16 08:43:18.768728

"""

# revision identifiers, used by Alembic.
revision = '2fb54e27efed'
down_revision = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('user', sa.Column('twitter_user_id', sa.Integer, unique=True))

def downgrade():
    op.drop_column('user', 'twitter_user_id')
