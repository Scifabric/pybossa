"""create category table

Revision ID: 47dd43c1491
Revises: 27bf0aefa49d
Create Date: 2013-05-21 10:41:43.548449

"""

# revision identifiers, used by Alembic.
revision = '47dd43c1491'
down_revision = '27bf0aefa49d'

from alembic import op
import sqlalchemy as sa
import datetime


def make_timestamp():
    now = datetime.datetime.utcnow()
    return now.isoformat()


def upgrade():
    op.create_table(
        'category',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', sa.Text, nullable=False, unique=True),
        sa.Column('short_name', sa.Text, nullable=False, unique=True),
        sa.Column('created', sa.Text, default=make_timestamp),
    )


def downgrade():
    op.drop_table('category')
