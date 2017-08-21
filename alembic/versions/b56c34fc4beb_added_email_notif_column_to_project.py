"""added email notif column to project

Revision ID: b56c34fc4beb
Revises: db2c89b01a81
Create Date: 2017-08-21 15:42:16.960970

"""

# revision identifiers, used by Alembic.
revision = 'b56c34fc4beb'
down_revision = 'db2c89b01a81'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('project', sa.Column('email_notif', sa.Boolean,
                                       default=False))


def downgrade():
    op.drop_column('project', 'email_notif')
