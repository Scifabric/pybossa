"""add pages table

Revision ID: 66ecf0b2aed5
Revises: c7476118715f
Create Date: 2019-06-01 16:10:06.519049

"""

# revision identifiers, used by Alembic.
revision = '66ecf0b2aed5'
down_revision = 'c7476118715f'

import datetime
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON, TIMESTAMP


def make_timestamp():
    now = datetime.datetime.utcnow()
    return now.isoformat()


def upgrade():
    op.create_table(
        'pages',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('slug', sa.Unicode(length=255), nullable=False),
        sa.Column('project_id',
                  sa.Integer,
                  sa.ForeignKey('project.id', ondelete='CASCADE'),
                  nullable=False),
        sa.Column('created', TIMESTAMP, default=make_timestamp),
        sa.Column('info', JSON, nullable=False),
        sa.Column('media_url', sa.Text),
        )


def downgrade():
    op.drop_table('pages')
