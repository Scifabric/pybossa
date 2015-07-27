"""text to JSON

Revision ID: 151b2f642877
Revises: ac115763654
Create Date: 2015-06-12 14:40:56.956657

"""

# revision identifiers, used by Alembic.
revision = '151b2f642877'
down_revision = 'ac115763654'

from alembic import op
import sqlalchemy as sa


def upgrade():
    query = 'ALTER TABLE project ALTER COLUMN info TYPE JSON USING info::JSON;'
    op.execute(query)
    query = 'ALTER TABLE "user" ALTER COLUMN info TYPE JSON USING info::JSON;'
    op.execute(query)
    query = 'ALTER TABLE task ALTER COLUMN info TYPE JSON USING info::JSON;'
    op.execute(query)
    query = 'ALTER TABLE task_run ALTER COLUMN info TYPE JSON USING info::JSON;'
    op.execute(query)


def downgrade():
    query = 'ALTER TABLE project ALTER COLUMN info TYPE TEXT USING info::TEXT;'
    op.execute(query)
    query = 'ALTER TABLE "user" ALTER COLUMN info TYPE TEXT USING info::TEXT;'
    op.execute(query)
    query = 'ALTER TABLE task ALTER COLUMN info TYPE TEXT USING info::TEXT;'
    op.execute(query)
    query = 'ALTER TABLE task_run ALTER COLUMN info TYPE TEXT USING info::TEXT;'
    op.execute(query)
