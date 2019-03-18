"""stat enum

Revision ID: 7b5f75fc2c08
Revises: e3f2a1bae1f3
Create Date: 2019-03-16 15:13:32.062464

"""

# revision identifiers, used by Alembic.
revision = '7b5f75fc2c08'
down_revision = 'e3f2a1bae1f3'

from alembic import op
import sqlalchemy as sa


def upgrade():
    query = '''CREATE TYPE statistic AS ENUM ('confusion_matrix', 'accuracy')'''
    op.execute(query)


def downgrade():
    query = '''DROP TYPE statistic'''
    op.execute(query)