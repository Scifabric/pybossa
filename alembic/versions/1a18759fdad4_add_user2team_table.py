"""Add User2Team Table

Revision ID: 1a18759fdad4
Revises: 483d70a10096
Create Date: 2013-05-27 13:41:55.153373

"""

# revision identifiers, used by Alembic.
revision = '1a18759fdad4'
down_revision = '483d70a10096'

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

