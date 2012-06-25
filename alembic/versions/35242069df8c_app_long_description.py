"""app long description field

Revision ID: 35242069df8c
Revises: 2fb54e27efed
Create Date: 2012-06-25 09:07:25.155464

"""

# revision identifiers, used by Alembic.
revision = '35242069df8c'
down_revision = '2fb54e27efed'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('app', sa.Column('long_description', sa.Unicode))

def downgrade():
    op.drop_column('app', 'long_description')
