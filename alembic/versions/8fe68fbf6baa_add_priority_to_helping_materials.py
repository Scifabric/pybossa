"""add priority to helping materials

Revision ID: 8fe68fbf6baa
Revises: 52209719b79e
Create Date: 2017-10-04 13:09:06.403945

"""

# revision identifiers, used by Alembic.
revision = '8fe68fbf6baa'
down_revision = '52209719b79e'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('helpingmaterial', sa.Column('priority', sa.Float, default=0))


def downgrade():
    op.drop_column('helpingmaterial', 'priority')
