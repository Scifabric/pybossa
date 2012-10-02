"""Change long_description to UnicodeText

Revision ID: 4f04ded45835
Revises: 3ee23961633
Create Date: 2012-10-04 13:34:16.345403

"""

# revision identifiers, used by Alembic.
revision = '4f04ded45835'
down_revision = '3ee23961633'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.alter_column('app', 'long_description', type_=sa.UnicodeText)
    pass


def downgrade():
    op.alter_column('app', 'long_description', type_=sa.Unicode)
    pass
