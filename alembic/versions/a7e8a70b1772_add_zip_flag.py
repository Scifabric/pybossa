"""add zip flag

Revision ID: a7e8a70b1772
Revises: 2498337aee4c
Create Date: 2017-11-07 09:45:22.115165

"""

# revision identifiers, used by Alembic.
revision = 'a7e8a70b1772'
down_revision = '2498337aee4c'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('project', sa.Column('zip_download', sa.Boolean,
                                       default=True))
    query = 'UPDATE "project" SET zip_download=true;'
    op.execute(query)


def downgrade():
    op.drop_column('project', 'zip_download')
