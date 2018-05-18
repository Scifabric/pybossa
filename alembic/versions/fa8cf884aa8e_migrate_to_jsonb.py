"""migrate to jsonb

Revision ID: fa8cf884aa8e
Revises: a7e8a70b1772
Create Date: 2018-02-05 16:13:38.229076

"""

# revision identifiers, used by Alembic.
revision = 'fa8cf884aa8e'
down_revision = 'a7e8a70b1772'

from alembic import op
import sqlalchemy as sa

tables = ['user', 'task', 'task_run', 'result', 'blogpost',
          'category', 'helpingmaterial', 'project', 'project_stats',
          'webhook']


def upgrade():
    for table in tables:
        if table == 'user':
            query = 'DROP MATERIALIZED VIEW users_rank'
            op.execute(query)
        if table != 'webhook':
            query = '''ALTER TABLE "%s" ALTER COLUMN info SET DATA TYPE jsonb USING info::jsonb;''' % table
        else:
            query = '''ALTER TABLE "%s" ALTER COLUMN payload SET DATA TYPE jsonb USING payload::jsonb;''' % table
        op.execute(query)


def downgrade():
    for table in tables:
        query = '''ALTER TABLE "%s" ALTER COLUMN info SET DATA TYPE json USING info::json;''' % table
        op.execute(query)
