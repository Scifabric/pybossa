"""Delete hidden column

Revision ID: 35f8b948e98d
Revises: 36fba9f9069d
Create Date: 2015-08-07 10:15:34.608398

"""

# revision identifiers, used by Alembic.
revision = '35f8b948e98d'
down_revision = '36fba9f9069d'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.drop_column('project', 'hidden')


def downgrade():
    op.add_column('project', sa.Column('hidden', sa.Integer, default=0))
