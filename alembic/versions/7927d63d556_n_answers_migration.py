"""n_answers migration

Revision ID: 7927d63d556
Revises: 1eb5febf4842
Create Date: 2014-08-08 14:02:36.738460

Delete the "n_answers" field from the "info" attribute/column as it is not used.
"""

# revision identifiers, used by Alembic.
revision = '7927d63d556'
down_revision = '1eb5febf4842'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column, select, bindparam
import json


def upgrade():
    task = table('task',
    column('id'),
    column('info')
    )
    conn = op.get_bind()
    query = select([task.c.id, task.c.info])
    tasks = conn.execute(query)
    update_values = []
    for row in tasks:
        info_data = row.info
        info_dict = json.loads(info_data)
        if info_dict.get('n_answers'):
            del info_dict['n_answers']
            update_values.append({'task_id': row.id, 'new_info': json.dumps(info_dict)})
    task_update = task.update().\
                       where(task.c.id == bindparam('task_id')).\
                       values(info=bindparam('new_info'))
    if len(update_values) > 0:
        conn.execute(task_update, update_values)


def downgrade():
    task = table('task',
    column('id'),
    column('info'),
    column('n_answers')
    )
    conn = op.get_bind()
    query = select([task.c.id, task.c.info, task.c.n_answers])
    tasks = conn.execute(query)
    update_values = []
    for row in tasks:
        info_data = row.info
        info_dict = json.loads(info_data)
        info_dict['n_answers'] = row.n_answers
        update_values.append({'task_id': row.id, 'new_info': json.dumps(info_dict)})
    task_update = task.update().\
                       where(task.c.id == bindparam('task_id')).\
                       values(info=bindparam('new_info'))
    if len(update_values) > 0:
        conn.execute(task_update, update_values)
