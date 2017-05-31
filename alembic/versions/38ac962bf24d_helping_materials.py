"""helping materials

Revision ID: 38ac962bf24d
Revises: 920578f0de9c
Create Date: 2017-05-30 13:55:36.845747

"""

# revision identifiers, used by Alembic.
revision = '38ac962bf24d'
down_revision = '920578f0de9c'

from alembic import op
import sqlalchemy as sa
import datetime
from sqlalchemy.dialects.postgresql import JSON, TIMESTAMP


def make_timestamp():
    now = datetime.datetime.utcnow()
    return now.isoformat()


def upgrade():
    op.create_table('helpingmaterial',
                    sa.Column('id', sa.Integer,
                              primary_key=True),
                    sa.Column('project_id', sa.Integer,
                              sa.ForeignKey('project.id',
                                            ondelete='CASCADE'),
                              nullable=False),
                    sa.Column('created', TIMESTAMP,
                              default=make_timestamp),
                    sa.Column('info', JSON, nullable=False),
                    sa.Column('media_url', sa.Text),
                    )


def downgrade():
    op.drop_table('helpingmaterial')
