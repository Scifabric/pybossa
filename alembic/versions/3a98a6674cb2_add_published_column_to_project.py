"""Add published column to project

Revision ID: 3a98a6674cb2
Revises: 35f8b948e98d
Create Date: 2015-08-07 10:24:31.558995

"""

# revision identifiers, used by Alembic.
revision = '3a98a6674cb2'
down_revision = '35f8b948e98d'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('project', sa.Column('published', sa.Boolean, default=False))
    query = 'UPDATE "project" SET published=false;'
    op.execute(query)
    op.alter_column('project', 'published', nullable=False)
    query = """UPDATE "project" SET published=true
               WHERE project.id IN
               (SELECT project.id FROM project, task WHERE
               project.id=task.project_id AND
               (project.info->>'task_presenter') IS NOT NULL AND
               (project.info->>'task_presenter')!=''
               GROUP BY project.id);"""
    op.execute(query)


def downgrade():
    op.drop_column('project', 'published')
