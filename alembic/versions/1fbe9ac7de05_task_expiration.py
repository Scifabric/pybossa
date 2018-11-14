"""task expiration

Revision ID: 1fbe9ac7de05
Revises: 39bf33f0914a
Create Date: 2018-11-12 18:19:55.393599

"""

# revision identifiers, used by Alembic.
revision = '1fbe9ac7de05'
down_revision = '39bf33f0914a'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('task', sa.Column('expiration', sa.DateTime, nullable=True))


def downgrade():
    op.drop_column('task', 'expiration')
