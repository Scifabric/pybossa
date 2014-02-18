"""Added RunData

Revision ID: 24669d291e60
Revises: 3f113ca6c186
Create Date: 2014-01-13 16:28:00.336953

"""

# revision identifiers, used by Alembic.
revision = '24669d291e60'
down_revision = '3f113ca6c186'

from alembic import op
import sqlalchemy as sa
import pybossa.model


def upgrade():
    op.create_table('run_data',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('created', sa.Text(), nullable=True),
    sa.Column('app_id', sa.Integer(), nullable=True),
    sa.Column('task_id', sa.Integer(), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('user_ip', sa.Text(), nullable=True),
    sa.Column('key', sa.Text(), nullable=True),
    sa.Column('amount', sa.Float(), nullable=True),
    sa.Column('info', pybossa.model.JSONType(), nullable=True),
    sa.ForeignKeyConstraint(['app_id'], ['app.id'], ),
    sa.ForeignKeyConstraint(['task_id'], ['task.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('run_data')
