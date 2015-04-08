"""Rename app table to project

Revision ID: aee7291c81
Revises: 4e435ff8ba74
Create Date: 2015-03-02 12:29:05.534510

"""

# revision identifiers, used by Alembic.
revision = 'aee7291c81'
down_revision = '4e435ff8ba74'

from alembic import op
import sqlalchemy as sa


def upgrade():
    # Rename table name
    query = 'ALTER TABLE app RENAME TO project;'
    op.execute(query)
    # Rename id sequence
    query = 'ALTER SEQUENCE app_id_seq RENAME TO project_id_seq;'
    op.execute(query)
    # Rename foreign keys in other tables
    query = 'ALTER TABLE blogpost RENAME app_id TO project_id;'
    op.execute(query)
    query = 'ALTER TABLE task RENAME app_id TO project_id;'
    op.execute(query)
    query = 'ALTER TABLE task_run RENAME app_id TO project_id;'
    op.execute(query)
    query = 'ALTER TABLE auditlog RENAME app_id TO project_id;'
    op.execute(query)
    query = 'ALTER TABLE auditlog RENAME app_short_name TO project_short_name;'
    op.execute(query)
    # Rename primary and unique keys
    query = 'ALTER TABLE app_pkey RENAME TO project_pkey;'
    op.execute(query)
    query = 'ALTER TABLE app_name_key RENAME TO project_name_key;'
    op.execute(query)
    query = 'ALTER TABLE app_short_name_key RENAME TO project_short_name_key;'
    op.execute(query)
    # Rename foreign key constraints project table. NOTE: requires PostgreSQL 9.2 or above
    query = 'ALTER TABLE project RENAME CONSTRAINT app_category_id_fkey TO project_category_id_fkey;'
    op.execute(query)
    query = 'ALTER TABLE project RENAME CONSTRAINT app_owner_id_fkey TO project_owner_id_fkey;'
    op.execute(query)
    # Rename foreign key constraints in other tables. NOTE: requires PostgreSQL 9.2 or above
    query = 'ALTER TABLE blogpost RENAME CONSTRAINT blogpost_app_id_fkey TO blogpost_project_id_fkey;'
    op.execute(query)
    query = 'ALTER TABLE task RENAME CONSTRAINT task_app_id_fkey TO task_project_id_fkey;'
    op.execute(query)
    query = 'ALTER TABLE task_run RENAME CONSTRAINT task_run_app_id_fkey TO task_run_project_id_fkey;'
    op.execute(query)


def downgrade():
    # Rename table name
    query = 'ALTER TABLE project RENAME TO app;'
    op.execute(query)
    # Rename id sequence
    query = 'ALTER SEQUENCE project_id_seq RENAME TO app_id_seq;'
    op.execute(query)
    # Rename foreign keys in other tables
    query = 'ALTER TABLE blogpost RENAME project_id TO app_id;'
    op.execute(query)
    query = 'ALTER TABLE task RENAME project_id TO app_id;'
    op.execute(query)
    query = 'ALTER TABLE task_run RENAME project_id TO app_id;'
    op.execute(query)
    query = 'ALTER TABLE auditlog RENAME project_id TO app_id;'
    op.execute(query)
    query = 'ALTER TABLE auditlog RENAME project_short_name TO app_short_name;'
    op.execute(query)
    # Rename primary and unique keys
    query = 'ALTER TABLE project_pkey RENAME TO app_pkey;'
    op.execute(query)
    query = 'ALTER TABLE project_name_key RENAME TO app_name_key;'
    op.execute(query)
    query = 'ALTER TABLE project_short_name_key RENAME TO app_short_name_key;'
    op.execute(query)
    # Rename foreign key constraints app table. NOTE: requires PostgreSQL 9.2 or above
    query = 'ALTER TABLE app RENAME CONSTRAINT project_category_id_fkey to app_category_id_fkey;'
    op.execute(query)
    query = 'ALTER TABLE app RENAME CONSTRAINT project_owner_id_fkey to app_owner_id_fkey;'
    op.execute(query)
    # Rename foreign key constraints in other tables. NOTE: requires PostgreSQL 9.2 or above
    query = 'ALTER TABLE blogpost RENAME CONSTRAINT blogpost_project_id_fkey TO blogpost_app_id_fkey;'
    op.execute(query)
    query = 'ALTER TABLE task RENAME CONSTRAINT task_project_id_fkey TO task_app_id_fkey;'
    op.execute(query)
    query = 'ALTER TABLE task_run RENAME CONSTRAINT task_run_project_id_fkey TO task_run_app_id_fkey;'
    op.execute(query)
