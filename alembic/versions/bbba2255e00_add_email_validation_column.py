"""add email validation column

Revision ID: bbba2255e00
Revises: 38a8a6299086
Create Date: 2014-12-16 14:18:45.290836

"""

# revision identifiers, used by Alembic.
revision = 'bbba2255e00'
down_revision = '38a8a6299086'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('user', sa.Column('valid_email', sa.Boolean, default=False))
    op.add_column('user', sa.Column('confirmation_email_sent', sa.Boolean, default=False))
    query = 'UPDATE "user" SET valid_email=false;'
    op.execute(query)
    query = 'UPDATE "user" SET confirmation_email_sent=false;'
    op.execute(query)


def downgrade():
    op.drop_column('user', 'valid_email')
    op.drop_column('user', 'confirmation_email_sent')
