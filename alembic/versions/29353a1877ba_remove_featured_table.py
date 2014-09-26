"""Remove featured table

Revision ID: 29353a1877ba
Revises: 537db2979434
Create Date: 2014-09-26 09:02:08.448275

"""

# revision identifiers, used by Alembic.
revision = '29353a1877ba'
down_revision = '537db2979434'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('app', sa.Column('featured', sa.Boolean, nullable=False, default=False))
    query = 'UPDATE "app" SET featured=true WHERE app.id IN (SELECT app_id FROM FEATURED);'
    op.execute(query)
    op.drop_table('featured')


def downgrade():
    op.create_table(
        'featured',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('created', sa.Text, default=make_timestamp),
        sa.Column('app_id', sa.Integer, ForeignKey('app.id'), unique=True)
    )
    query = 'INSERT INTO "featured" (app_id) VALUES (SELECT id FROM "app" WHERE featured=true);'
    op.execute(query)
    op.drop_column('app', 'featured')
