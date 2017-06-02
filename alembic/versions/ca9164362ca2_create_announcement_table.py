"""Create announcement table

Revision ID: ca9164362ca2
Revises: 920578f0de9c
Create Date: 2017-05-26 12:55:21.180329

"""

# revision identifiers, used by Alembic.
revision = 'ca9164362ca2'
down_revision = '38ac962bf24d'

from alembic import op
import sqlalchemy as sa


def make_timestamp():
    now = datetime.datetime.utcnow()
    return now.isoformat()


def upgrade():
    op.create_table(
        'announcement',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('title', sa.Unicode(length=255), nullable=False),
        sa.Column('body', sa.UnicodeText, nullable=False),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('user.id')),
        sa.Column('created', sa.Text, default=make_timestamp),
    )

def downgrade():
    op.drop_table('announcement')