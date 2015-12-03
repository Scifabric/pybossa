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


def upgrade():
    op.drop_column('project', 'completed')


def downgrade():
    op.add_column('project', sa.Column('completed', sa.Boolean, default=False))
    query = 'UPDATE project SET completed=false;'
    op.execute(query)
    op.alter_column('project', 'completed', nullable=False)

    update_completed = '''
        WITH completed_tasks AS (
        SELECT project.id, COUNT(task.id) as n_completed_tasks FROM project, task
        WHERE task.state='completed' AND task.project_id=project.id
        GROUP BY project.id
        ), total_tasks AS (
        SELECT project.id, COUNT(task.id) as n_tasks FROM project, task
        WHERE task.project_id=project.id
        GROUP BY project.id
        )
        UPDATE project SET completed=true WHERE project.id IN (
            SELECT total_tasks.id
            FROM completed_tasks INNER JOIN total_tasks ON completed_tasks.id=total_tasks.id
        );
    '''

    op.execute(update_completed)
    # sql = sa.sql.text('''SELECT COUNT(task.id) AS n_completed_tasks FROM task
    #             WHERE task.project_id=:project_id AND task.state=\'completed\';''')
    # sql = sa.sql.text('''SELECT COUNT(task.id) AS n_tasks FROM task
    #               WHERE task.project_id=:project_id''')
