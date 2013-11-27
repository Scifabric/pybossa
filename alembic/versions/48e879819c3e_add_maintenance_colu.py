"""Add maintenance column to App

Revision ID: 48e879819c3e
Revises: 3f113ca6c186
Create Date: 2013-11-27 17:46:22.921609

"""

# revision identifiers, used by Alembic.
revision = '48e879819c3e'
down_revision = '3f113ca6c186'

from alembic import op
import sqlalchemy as sa

def upgrade():
    op.add_column('app', sa.Column('maintenance', sa.Integer))

def downgrade():
    op.drop_column('app', 'maintenance')
