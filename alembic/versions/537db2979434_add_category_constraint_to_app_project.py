"""Add category constraint to app/project

Revision ID: 537db2979434
Revises: 7927d63d556
Create Date: 2014-09-25 10:39:57.300726

"""

# revision identifiers, used by Alembic.
revision = '537db2979434'
down_revision = '7927d63d556'

from alembic import op
import sqlalchemy as sa


def upgrade():
    query = 'UPDATE app SET category_id=(SELECT id FROM category ORDER BY id asc limit 1) WHERE app.category_id is NULL;'
    op.execute(query)
    op.alter_column('app', 'category_id', nullable=False)


def downgrade():
    op.alter_column('app', 'category_id', nullable=True)
