"""GDPR restrict processing

Revision ID: 174eb928136a
Revises: d5b07c8f0893
Create Date: 2018-05-14 11:21:55.138387

"""

# revision identifiers, used by Alembic.
revision = '174eb928136a'
down_revision = 'd5b07c8f0893'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('user', sa.Column('restrict', sa.Boolean, default=False))
    sql = 'update "user" set restrict=false'
    op.execute(sql)


def downgrade():
    op.drop_column('user', 'restrict')
