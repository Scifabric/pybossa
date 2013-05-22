"""Add table team

Revision ID: f74b07be6fd
Revises: 27bf0aefa49d
Create Date: 2013-04-30 17:29:09.503603

"""

# revision identifiers, used by Alembic.
revision = 'f74b07be6fd'
down_revision = '27bf0aefa49d'

from alembic import op
import sqlalchemy as sa
from sqlalchemy import ForeignKey

def make_timestamp():
    now = datetime.datetime.now()
    return now.isoformat()

def upgrade():
   op.create_table(
        'team',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('created', sa.Text, default=make_timestamp),
        sa.Column('name', sa.String(50), nullable=False),
        sa.Column('description', sa.Unicode(200)),
        sa.Column('owner', sa.Integer, ForeignKey('user.id'), unique=True),
        sa.Column('public', sa.Boolean, default=False )
    )

def downgrade():
    op.drop_table('team')

