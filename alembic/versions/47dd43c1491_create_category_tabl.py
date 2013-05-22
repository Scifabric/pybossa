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
        sa.Column('description', sa.Text, nullable=False),
        sa.Column('created', sa.Text, default=make_timestamp),
    )

    # Add two categories
    query = 'INSERT INTO category (name, short_name, description) VALUES (\'Thinking\', \'thinking\', \'Applications where you can help using your skills\')'
    op.execute(query)
    query = 'INSERT INTO category  (name, short_name, description) VALUES (\'Sensing\', \'sensing\', \'Applications where you can help gathering data\')'
    op.execute(query)


def downgrade():
    op.drop_table('category')
