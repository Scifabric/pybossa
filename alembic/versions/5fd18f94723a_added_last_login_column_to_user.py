"""added last_login column to user

Revision ID: 5fd18f94723a
Revises: 25927be2b965
Create Date: 2017-06-28 10:55:57.569441

"""

# revision identifiers, used by Alembic.
revision = '5fd18f94723a'
down_revision = '25927be2b965'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('user', sa.Column('last_login', sa.Text))
    query = """UPDATE "user" SET last_login=to_char(current_timestamp, 'YYYY-MM-DD"T"HH24:MI:SS.US');"""
    op.execute(query)


def downgrade():
    op.drop_column('user', 'last_login')
