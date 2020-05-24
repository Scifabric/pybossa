"""Add new notify column to user

Revision ID: a791f9de9ac3
Revises: 66ecf0b2aed5
Create Date: 2020-05-23 16:01:27.795514

"""

# revision identifiers, used by Alembic.
revision = 'a791f9de9ac3'
down_revision = '66ecf0b2aed5'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('user', sa.Column('notified_at', sa.Date, default=None))


def downgrade():
    op.drop_column('user', 'notified_at')
