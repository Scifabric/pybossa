"""add table constraints to user locale and privacy mode

Revision ID: 46c3f68e950a
Revises: 4ad4fddc76f8
Create Date: 2014-03-08 09:53:09.049736

"""

# revision identifiers, used by Alembic.
revision = '46c3f68e950a'
down_revision = '4ad4fddc76f8'

from alembic import op
import sqlalchemy as sa


def upgrade():
    query = 'UPDATE "user" SET locale=\'en\';'
    op.execute(query)
    op.alter_column('user', 'locale', nullable=False)
    op.alter_column('user', 'privacy_mode', nullable=False)



def downgrade():
    op.alter_column('user', 'locale', nullable=True)
    op.alter_column('user', 'privacy_mode', nullable=True)
