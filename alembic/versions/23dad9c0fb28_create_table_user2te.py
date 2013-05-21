"""create table user2team

Revision ID: 23dad9c0fb28
Revises: 47f7c3eaf550
Create Date: 2013-05-09 10:47:29.073150

"""

# revision identifiers, used by Alembic.
revision = '23dad9c0fb28'
down_revision = '47f7c3eaf550'

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
       sa.Column('status', sa.Integer, default=0),

       sa.PrimaryKeyConstraint('user_id','team_id')
    )

def downgrade():
    op.drop_table('user2team')

