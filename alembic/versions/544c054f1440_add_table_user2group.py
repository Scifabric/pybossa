"""Add Table User2Group

Revision ID: 544c054f1440
Revises: f74b07be6fd
Create Date: 2013-04-30 17:32:53.151219

"""

# revision identifiers, used by Alembic.
revision = '544c054f1440'
down_revision = 'f74b07be6fd'

from alembic import op
import sqlalchemy as sa
from sqlalchemy import ForeignKey

def make_timestamp():
    now = datetime.datetime.now()
    return now.isoformat()

def upgrade():
   op.create_table(
       'user2team',
       sa.Column('user_id', sa.Integer, ForeignKey('user.id'), unique=False),
       sa.Column('team_id', sa.Integer, ForeignKey('team.id'), unique=False),
       sa.Column('created', sa.Text, default=make_timestamp),

       sa.PrimaryKeyConstraint('user_id','team_id')
    )

def downgrade():
    op.drop_table('user2team')


