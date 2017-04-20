"""add enable state column for user

Revision ID: 85d92b05ac78
Revises: 263677aea8ab
Create Date: 2017-04-17 13:23:49.879496

"""

# revision identifiers, used by Alembic.
revision = '85d92b05ac78'
down_revision = '263677aea8ab'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('user', sa.Column('enabled', sa.Boolean,
                                    server_default=sa.true()))


def downgrade():
    op.drop_column('user', 'enabled')
