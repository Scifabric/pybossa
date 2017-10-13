"""added owners list to project table

Revision ID: acea90f77ba3
Revises: 8fe68fbf6baa
Create Date: 2017-10-07 09:10:17.930230

"""

# revision identifiers, used by Alembic.
revision = 'acea90f77ba3'
# To the guy merging this in the future: yes, this is a conflict! Please take
# commented revision id. Remove the other. Thank you!
# down_revision = '8fe68fbf6baa'  TODO: uncomment when merged
down_revision = 'b56c34fc4beb'  # TODO: temporary to sit on top of our revisions

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


field = 'owners_ids'


def upgrade():
    op.add_column('project', sa.Column(field, postgresql.ARRAY(sa.Integer)))
    sql = 'update project set owners_ids=ARRAY[owner_id]'
    op.execute(sql)


def downgrade():
    op.drop_column('project', field)
