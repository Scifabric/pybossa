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


def make_timestamp():
    now = datetime.datetime.utcnow()
    return now.isoformat()


def upgrade():
    op.create_table(
    'pages',
    sa.Column('id', sa.Integer, primary_key=True),
    sa.Column('title', sa.Unicode(length=255), nullable=False),
    sa.Column('body', sa.UnicodeText, nullable=False),
    sa.Column('app_id', sa.Integer, sa.ForeignKey('app.id', ondelete='CASCADE'), nullable=False),
    sa.Column('user_id', sa.Integer, sa.ForeignKey('user.id')),
    sa.Column('created', sa.Text, default=make_timestamp),
    )



def downgrade():
   op.drop_table('pages')
