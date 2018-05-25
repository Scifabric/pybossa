"""unsubscribe gdpr

Revision ID: d5b07c8f0893
Revises: d317dc38cf39
Create Date: 2018-04-20 11:31:48.786659

"""

# revision identifiers, used by Alembic.
revision = 'd5b07c8f0893'
down_revision = 'd317dc38cf39'

from alembic import op
import sqlalchemy as sa


def upgrade():
    sql = 'update "user" set subscribed=false'
    op.execute(sql)


def downgrade():
    sql = 'update "user" set subscribed=true'
    op.execute(sql)
