"""add hidden column

Revision ID: 3429ea9ee18c
Revises: 41eb366742cf
Create Date: 2017-02-27 16:49:08.458012

"""

# revision identifiers, used by Alembic.
revision = '3429ea9ee18c'
down_revision = '41eb366742cf'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('project', sa.Column('hidden', sa.Boolean))
    op.execute('UPDATE project SET hidden=false')
    op.alter_column('project', 'hidden', nullable=False)


def downgrade():
    op.drop_column('project', 'hidden')

