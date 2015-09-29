"""delete unused project columns

Revision ID: 36fba9f9069d
Revises: 151b2f642877
Create Date: 2015-08-07 09:45:22.044720

"""

# revision identifiers, used by Alembic.
revision = '36fba9f9069d'
down_revision = '151b2f642877'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.drop_column('project', 'time_estimate')
    op.drop_column('project', 'time_limit')
    op.drop_column('project', 'calibration_frac')
    op.drop_column('project', 'bolt_course_id')
    op.drop_column('project', 'long_tasks')


def downgrade():
    op.add_column('project', sa.Column('time_estimate', sa.Integer, default=0))
    op.add_column('project', sa.Column('time_limit', sa.Integer, default=0))
    op.add_column('project', sa.Column('calibration_frac', sa.Float, default=0))
    op.add_column('project', sa.Column('bolt_course_id', sa.Integer, default=0))
    op.add_column('project', sa.Column('long_tasks', sa.Integer, default=0))
