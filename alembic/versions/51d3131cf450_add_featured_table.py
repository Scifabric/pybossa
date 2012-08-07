"""add featured table

Revision ID: 51d3131cf450
Revises: 9341dfd1b21
Create Date: 2012-07-31 17:15:38.969627

"""


# revision identifiers, used by Alembic.
revision = '51d3131cf450'
down_revision = '9341dfd1b21'

from alembic import op
import sqlalchemy as sa
from sqlalchemy import ForeignKey


def make_timestamp():
    now = datetime.datetime.now()
    return now.isoformat()


def upgrade():
    op.create_table(
        'featured',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('created', sa.Text, default=make_timestamp),
        sa.Column('app_id', sa.Integer, ForeignKey('app.id'), unique=True)
    )


def downgrade():
    op.drop_table('featured')
