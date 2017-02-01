"""added co-owners feature

Revision ID: 15631664d47c
Revises: 8ce9b3da799e
Create Date: 2017-02-01 10:35:06.053779

"""

# revision identifiers, used by Alembic.
revision = '15631664d47c'
down_revision = '8ce9b3da799e'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    op.create_table('project_coowner',
    sa.Column('project_id', sa.INTEGER(), nullable=False, primary_key=True),
    sa.Column('coowner_id', sa.INTEGER(), nullable=False, primary_key=True),
    )

    op.create_foreign_key(u'project_coowner_coowner_id_fkey', 'project_coowner', 'user', ['coowner_id'], ['id'], ondelete=u'CASCADE')
    op.create_foreign_key(u'project_coowner_project_id_fkey', 'project_coowner', 'project', ['project_id'], ['id'], ondelete=u'CASCADE')


def downgrade():
    op.drop_constraint(u'project_coowner_coowner_id_fkey', 'project_coowner', type_='foreignkey')
    op.drop_constraint(u'project_coowner_project_id_fkey', 'project_coowner', type_='foreignkey')
    op.drop_constraint('project_coowner_pkey', table_name='project_coowner', type='primary')

    op.drop_table('project_coowner')