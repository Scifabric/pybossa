"""add app category field

Revision ID: 3f113ca6c186
Revises: 47dd43c1491
Create Date: 2013-05-21 14:07:25.855929

"""

# revision identifiers, used by Alembic.
revision = '3f113ca6c186'
down_revision = '47dd43c1491'

from alembic import op
import sqlalchemy as sa


field = 'category_id'


def upgrade():
    op.add_column('app', sa.Column(field, sa.Integer, sa.ForeignKey('category.id')))


def downgrade():
    op.drop_column('app', field)
