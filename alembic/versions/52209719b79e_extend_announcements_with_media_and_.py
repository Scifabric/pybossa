"""extend announcements with media and info entries

Revision ID: 52209719b79e
Revises: 5a633236f075
Create Date: 2017-08-30 09:48:07.507323

"""

# revision identifiers, used by Alembic.
revision = '52209719b79e'
down_revision = '5a633236f075'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON

def make_timestamp():
    now = datetime.datetime.utcnow()
    return now.isoformat()


def upgrade():
    op.add_column('announcement', sa.Column('media_url', sa.String))
    op.add_column('announcement', sa.Column('info', JSON))
    op.add_column('announcement', sa.Column('published', sa.Boolean, default=False))
    op.add_column('announcement', sa.Column('updated', sa.Text,
                                       default=make_timestamp))
    sql = 'update announcement set published=true'
    op.execute(sql)


def downgrade():
    op.drop_column('announcement', 'media_url')
    op.drop_column('announcement', 'info')
    op.drop_column('announcement', 'published')
    op.drop_column('announcement', 'updated')
