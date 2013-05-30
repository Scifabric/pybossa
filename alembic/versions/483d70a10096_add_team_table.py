"""Add Team Table

Revision ID: 483d70a10096
Revises: 3f113ca6c186
Create Date: 2013-05-27 13:38:03.814113

"""

# revision identifiers, used by Alembic.
revision = '483d70a10096'
down_revision = '3f113ca6c186'


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
        sa.Column('owner_id', sa.Integer, ForeignKey('user.id')),
        sa.Column('public', sa.Boolean, default=False )
    )

def downgrade():
    op.drop_table('team')
