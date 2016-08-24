"""Add amnesty user id column

Revision ID: d42631c07887
Revises: 4f12d8650050
Create Date: 2016-07-25 09:05:40.724455

"""

# revision identifiers, used by Alembic.
revision = 'd42631c07887'
down_revision = '4f12d8650050'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('user', sa.Column('amnesty_user_id', sa.Integer, unique=True))


def downgrade():
    op.drop_column('user', 'amnesty_user_id')