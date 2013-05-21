"""create table team

Revision ID: 47f7c3eaf550
Revises: 27bf0aefa49d
Create Date: 2013-05-09 10:46:10.444961

"""

# revision identifiers, used by Alembic.
revision = '47f7c3eaf550'
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
