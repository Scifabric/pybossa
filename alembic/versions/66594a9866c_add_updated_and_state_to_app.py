"""add updated and state to app

Revision ID: 66594a9866c
Revises: 29353a1877ba
Create Date: 2014-10-23 10:53:15.357562

"""

# revision identifiers, used by Alembic.
revision = '66594a9866c'
down_revision = '29353a1877ba'

from alembic import op
import sqlalchemy as sa
import datetime

def make_timestamp():
    now = datetime.datetime.utcnow()
    return now.isoformat()

def upgrade():
    op.add_column('app', sa.Column('updated', sa.Text, default=make_timestamp))
    op.add_column('app', sa.Column('contacted', sa.Boolean, default=False))
    op.add_column('app', sa.Column('completed', sa.Boolean, default=False))
    # Update all projects to the day the migration is run
    query = "UPDATE app SET updated='%s'" % make_timestamp()
    op.execute(query)
    # Update the state of the projects
    # Put all of them to false
    query = 'UPDATE app SET completed=false'
    op.execute(query)
    # Update to completed those that are not included in the set
    query = "UPDATE app SET completed=true WHERE id NOT IN (SELECT app_id FROM task WHERE state!='completed' OR state IS NULL GROUP BY app_id)"
    op.execute(query)
    # Update to not completed those that do not have any task
    query = "UPDATE app SET completed=false WHERE id NOT IN (SELECT app_id FROM task group by app_id)"
    op.execute(query)



def downgrade():
    op.drop_column('app', 'updated')
    op.drop_column('app', 'contacted')
    op.drop_column('app', 'completed')
