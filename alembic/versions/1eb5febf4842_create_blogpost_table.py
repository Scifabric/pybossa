"""Create blogpost table

Revision ID: 1eb5febf4842
Revises: 3da51a88205a
Create Date: 2014-04-07 15:18:09.024341

"""

# revision identifiers, used by Alembic.
revision = '1eb5febf4842'
down_revision = '3da51a88205a'

from alembic import op
import sqlalchemy as sa
import datetime


def make_timestamp():
    now = datetime.datetime.utcnow()
    return now.isoformat()


def upgrade():
    op.create_table(
    'blogpost',
    sa.Column('id', sa.Integer, primary_key=True),
    sa.Column('title', sa.Unicode(length=255), nullable=False),
    sa.Column('body', sa.UnicodeText, nullable=False),
    sa.Column('app_id', sa.Integer, sa.ForeignKey('app.id', ondelete='CASCADE'), nullable=False),
    sa.Column('user_id', sa.Integer, sa.ForeignKey('user.id')),
    sa.Column('created', sa.Text, default=make_timestamp),
    )


def downgrade():
   op.drop_table('blogpost')
