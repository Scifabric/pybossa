"""n_answers into task

Revision ID: 3ee23961633
Revises: 25e478de8a63
Create Date: 2012-09-13 10:40:22.345634

"""

# revision identifiers, used by Alembic.
revision = '3ee23961633'
down_revision = '25e478de8a63'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('task', sa.Column('n_answers', sa.Integer, default=30))


def downgrade():
    op.drop_column('task', 'n_answers')
