"""Add webhooks table

Revision ID: 4a571e217ab8
Revises: 3a98a6674cb2
Create Date: 2015-08-17 16:52:28.279419

"""

# revision identifiers, used by Alembic.
revision = '4a571e217ab8'
down_revision = '3a98a6674cb2'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON
import datetime

def make_timestamp():
    now = datetime.datetime.utcnow()
    return now.isoformat()

def upgrade():
    op.create_table('webhook',
                    sa.Column('id', sa.Integer, primary_key=True),
                    sa.Column('created', sa.Text, default=make_timestamp),
                    sa.Column('updated', sa.Text, default=make_timestamp),
                    sa.Column('project_id', sa.Integer,
                              sa.ForeignKey('project.id')),
                    sa.Column('payload', JSON),
                    sa.Column('response', sa.Text),
                    sa.Column('response_status_code', sa.Integer)
                    )


def downgrade():
    op.drop_table('webhook')
