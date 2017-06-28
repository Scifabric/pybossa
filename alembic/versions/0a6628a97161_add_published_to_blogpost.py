"""add published to blogpost

Revision ID: 0a6628a97161
Revises: c2c7704dbc13
Create Date: 2017-06-28 17:03:54.846810

"""

# revision identifiers, used by Alembic.
revision = '0a6628a97161'
down_revision = 'c2c7704dbc13'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('blogpost', sa.Column('published', sa.Boolean, default=False))
    sql = 'update blogpost set published=true'
    op.execute(sql)



def downgrade():
    op.drop_column('blogpost', 'published')
