"""add facebook user id

Revision ID: a0d7c1872e
Revises: 35242069df8c
Create Date: 2012-06-29 12:18:38.475096

"""

# revision identifiers, used by Alembic.
revision = 'a0d7c1872e'
down_revision = '35242069df8c'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('user', sa.Column('facebook_user_id', sa.Integer, unique=True))

def downgrade():
    op.drop_column('user', 'facebook_user_id')
