"""add ldap field to user

Revision ID: 2498337aee4c
Revises: acea90f77ba3
Create Date: 2017-10-23 09:58:37.710941

"""

# revision identifiers, used by Alembic.
revision = '2498337aee4c'
down_revision = 'acea90f77ba3'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('user', sa.Column('ldap', sa.String, unique=True))


def downgrade():
    op.drop_column('user', 'ldap')
