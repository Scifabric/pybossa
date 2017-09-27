"""Add info to category

Revision ID: 4e795a38cd4b
Revises: 0a6628a97161
Create Date: 2017-08-15 12:21:47.441561

"""

# revision identifiers, used by Alembic.
revision = '4e795a38cd4b'
down_revision = '0a6628a97161'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON

def upgrade():
    op.add_column('category', sa.Column('info', JSON))


def downgrade():
    op.drop_column('category', 'info')
