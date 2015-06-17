"""remove_completed_column_from_project

Revision ID: ac115763654
Revises: aee7291c81
Create Date: 2015-06-17 16:22:58.251554

"""

# revision identifiers, used by Alembic.
revision = 'ac115763654'
down_revision = 'aee7291c81'

from alembic import op
import sqlalchemy as sa
from pybossa.cache.projects import overall_progress


def upgrade():
    op.drop_column('project', 'completed')


def downgrade():
    op.add_column('project', sa.Column('completed', sa.Boolean, default=False))
    query = 'UPDATE project SET completed=false;'
    op.execute(query)
    op.alter_column('project', 'completed', nullable=False)
