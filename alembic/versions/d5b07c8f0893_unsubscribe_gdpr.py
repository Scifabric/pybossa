"""unsubscribe gdpr

Revision ID: d5b07c8f0893
Revises: 6f137b29f917
Create Date: 2018-04-20 11:31:48.786659

"""

# revision identifiers, used by Alembic.
revision = 'd5b07c8f0893'
down_revision = '6f137b29f917'

from alembic import op
import sqlalchemy as sa


def upgrade():
    sql = 'update "user" set subscribed=false'
    op.execute(sql)


def downgrade():
    sql = 'update "user" set subscribed=true'
    op.execute(sql)
