"""add app category field

Revision ID: 3f113ca6c186
Revises: 47dd43c1491
Create Date: 2013-05-21 14:07:25.855929

"""

# revision identifiers, used by Alembic.
revision = '3f113ca6c186'
down_revision = '47dd43c1491'

from alembic import op
import sqlalchemy as sa


field = 'category_id'


def upgrade():
    op.add_column('app', sa.Column(field, sa.Integer, sa.ForeignKey('category.id')))
    # Assign First Category to Published Apps but not draft
    query = 'UPDATE app SET category_id=1 FROM task WHERE app.info LIKE(\'%task_presenter%\') AND task.app_id=app.id AND app.hidden=0'
    op.execute(query)


def downgrade():
    op.drop_column('app', field)
