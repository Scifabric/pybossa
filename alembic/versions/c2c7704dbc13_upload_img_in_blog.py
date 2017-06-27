"""Upload img in Blog

Revision ID: c2c7704dbc13
Revises: d1add5e3e65e
Create Date: 2017-06-27 10:41:26.856029

"""

# revision identifiers, used by Alembic.
revision = 'c2c7704dbc13'
down_revision = 'd1add5e3e65e'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON

field = 'media_url'


def upgrade():
    op.add_column('blogpost', sa.Column(field, sa.String))
    op.add_column('blogpost', sa.Column('info', JSON))


def downgrade():
    op.drop_column('blogpost', field)
    op.drop_column('blogpost', 'info')
