"""Add audit log table

Revision ID: f8bc21a0be7
Revises: 188c85878d36
Create Date: 2014-11-26 13:19:12.463507

"""

# revision identifiers, used by Alembic.
revision = 'f8bc21a0be7'
down_revision = '188c85878d36'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table('auditlog',
                    sa.Column('id', sa.Integer, primary_key=True),
                    sa.Column('app_id', sa.Integer, nullable=False),
                    sa.Column('app_short_name', sa.Text, nullable=False),
                    sa.Column('user_id', sa.Integer, nullable=False),
                    sa.Column('user_name', sa.Text, nullable=False),
                    sa.Column('created', sa.Text, nullable=False),
                    sa.Column('action', sa.Text, nullable=False),
                    sa.Column('caller', sa.Text, nullable=False),
                    sa.Column('attribute', sa.Text, nullable=False),
                    sa.Column('old_value', sa.Text),
                    sa.Column('new_value', sa.Text))


def downgrade():
    op.drop_table('auditlog')
