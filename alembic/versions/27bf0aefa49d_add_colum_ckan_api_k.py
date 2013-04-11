"""add colum ckan_api key field to user

Revision ID: 27bf0aefa49d
Revises: 9f0b1e842d8
Create Date: 2013-04-11 12:03:51.348130

"""

# revision identifiers, used by Alembic.
revision = '27bf0aefa49d'
down_revision = '9f0b1e842d8'

from alembic import op
import sqlalchemy as sa


field = 'ckan_api'


def upgrade():
    op.add_column('user', sa.Column(field, sa.String))


def downgrade():
    op.drop_column('user', field)
