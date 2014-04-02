"""html to markdown in app long_description

Revision ID: 43c3a523af05
Revises: 3da51a88205a
Create Date: 2014-03-31 15:47:57.151875

"""

# revision identifiers, used by Alembic.
revision = '43c3a523af05'
down_revision = '3da51a88205a'

from alembic import op
import sqlalchemy as sa
from html2text import html2text
from flask.ext.misaka import markdown


def upgrade():
    conn = op.get_bind()
    query = 'SELECT id, long_description FROM "app";'
    query_result = conn.execute(query)
    old_descriptions = query_result.fetchall()
    for old_desc in old_descriptions:
        new_descritpion = html2text(old_desc.long_description)
        query = ("UPDATE \"app\" SET long_description=\'%s\' WHERE id=%s;"
                % (new_descritpion, old_desc.id))
        conn.execute(query)



def downgrade():
    conn = op.get_bind()
    query = 'SELECT id, long_description FROM "app";'
    query_result = conn.execute(query)
    old_descriptions = query_result.fetchall()
    for old_desc in old_descriptions:
        new_descritpion = markdown(old_desc.long_description)
        query = ("UPDATE \"app\" SET long_description=\'%s\' WHERE id=%s;"
                % (new_descritpion, old_desc.id))
        conn.execute(query)
