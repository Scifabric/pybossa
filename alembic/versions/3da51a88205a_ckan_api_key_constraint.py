"""ckan api key constraint

Revision ID: 3da51a88205a
Revises: 46c3f68e950a
Create Date: 2014-04-01 11:33:01.394220

"""

# revision identifiers, used by Alembic.
revision = '3da51a88205a'
down_revision = '46c3f68e950a'

from alembic import op
import sqlalchemy as sa


def upgrade():
    query = '''UPDATE "user"
                 SET ckan_api=null
                 WHERE id IN (SELECT id 
                    FROM (SELECT id, row_number() over (partition BY ckan_api ORDER BY id) AS rnum
                          FROM "user") t
               WHERE t.rnum > 1);
            '''
    op.execute(query)
    op.create_unique_constraint('ckan_api_uq', 'user', ['ckan_api'])


def downgrade():
    op.drop_constraint('ckan_api_uq', 'user')
