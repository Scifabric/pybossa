"""User: create column language

Revision ID: 17861b8c36c6
Revises: 2a9a0ccb45fc
Create Date: 2013-03-13 16:46:10.519331

"""

# revision identifiers, used by Alembic.
revision = '17861b8c36c6'
down_revision = '2a9a0ccb45fc'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('user', 
        sa.Column('language', sa.String)
    )
    pass

def downgrade():
    pass
