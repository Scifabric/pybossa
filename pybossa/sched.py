# -*- coding: utf8 -*-
# This file is part of PYBOSSA.
#
# Copyright (C) 2015 Scifabric LTD.
#
# PYBOSSA is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# PYBOSSA is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with PYBOSSA.  If not, see <http://www.gnu.org/licenses/>.
"""Scheduler module for PYBOSSA tasks."""
from sqlalchemy.sql import text
from pybossa.model.task import Task
from pybossa.model.task_run import TaskRun
from pybossa.core import db
import random


session = db.slave_session


def new_task(project_id, sched, user_id=None, user_ip=None,
             external_uid=None, offset=0, limit=1):
    """Get a new task by calling the appropriate scheduler function."""
    sched_map = {
        'default': get_depth_first_task,
        'breadth_first': get_breadth_first_task,
        'depth_first': get_depth_first_task,
        'incremental': get_incremental_task}
    scheduler = sched_map.get(sched, sched_map['default'])
    return scheduler(project_id, user_id, user_ip, external_uid, offset=offset, limit=limit)


def get_breadth_first_task(project_id, user_id=None, user_ip=None,
                           external_uid=None, offset=0, limit=1):
    """Get a new task which have the least number of task runs.

    It excludes the current user.

    Note that it **ignores** the number of answers limit for efficiency reasons
    (this is not a big issue as all it means is that you may end up with some
    tasks run more than is strictly needed!)
    """
    if user_id and not user_ip and not external_uid:
        sql = text('''
                   SELECT task.id, COUNT(task_run.task_id) AS taskcount
                   FROM task
                   LEFT JOIN task_run ON (task.id = task_run.task_id)
                   WHERE NOT EXISTS
                   (SELECT 1 FROM task_run WHERE project_id=:project_id AND
                   user_id=:user_id AND task_id=task.id)
                   AND task.project_id=:project_id AND task.state !='completed'
                   group by task.id ORDER BY taskcount, id ASC LIMIT :limit OFFSET :offset;
                   ''')
        rows = session.execute(sql,
                               dict(project_id=project_id, user_id=user_id,
                                    limit=limit, offset=offset))
    else:
        if not user_ip:  # pragma: no cover
            user_ip = '127.0.0.1'
        if user_ip and not external_uid:
            sql = text('''
                       SELECT task.id, COUNT(task_run.task_id) AS taskcount
                       FROM task
                       LEFT JOIN task_run ON (task.id = task_run.task_id)
                       WHERE NOT EXISTS
                       (SELECT 1 FROM task_run WHERE project_id=:project_id AND
                       user_ip=:user_ip AND task_id=task.id)
                       AND task.project_id=:project_id AND task.state !='completed'
                       group by task.id ORDER BY taskcount, id ASC LIMIT :limit OFFSET :offset;
                       ''')
            rows = session.execute(sql,
                                   dict(project_id=project_id, user_ip=user_ip, 
                                        limit=limit, offset=offset))
        else:
            sql = text('''
                       SELECT task.id, COUNT(task_run.task_id) AS taskcount
                       FROM task
                       LEFT JOIN task_run ON (task.id = task_run.task_id)
                       WHERE NOT EXISTS
                       (SELECT 1 FROM task_run WHERE project_id=:project_id AND
                       external_uid=:external_uid AND task_id=task.id)
                       AND task.project_id=:project_id AND task.state !='completed'
                       group by task.id ORDER BY taskcount, id ASC LIMIT :limit OFFSET :offset;
                       ''')
            rows = session.execute(sql,
                                   dict(project_id=project_id,
                                        external_uid=external_uid, 
                                        limit=limit, offset=offset))

    task_ids = [x[0] for x in rows]
    tasks = session.query(Task).filter(Task.id.in_(task_ids)).all()
    return tasks


def get_depth_first_task(project_id, user_id=None, user_ip=None,
                         external_uid=None, offset=0, limit=1):
    """Get a new task for a given project."""
    candidate_task_ids = get_candidate_task_ids(project_id, user_id,
                                                user_ip, external_uid, limit, offset)
    tasks = session.query(Task).filter(Task.id.in_(candidate_task_ids)).all()
    return tasks


def get_incremental_task(project_id, user_id=None, user_ip=None,
                         external_uid=None, offset=0, limit=1):
    """Get a new task for a given project with its last given answer.

    It is an important strategy when dealing with large tasks, as
    transcriptions.
    """
    candidate_task_ids = get_candidate_task_ids(project_id, user_id, user_ip,
                                                external_uid, limit, offset)
    total_remaining = len(candidate_task_ids)
    if total_remaining == 0:
        return None
    rand = random.randrange(0, total_remaining)
    task_id = candidate_task_ids[rand]
    task = session.query(Task).get(task_id)
    # Find last answer for the task
    q = session.query(TaskRun)\
        .filter(TaskRun.task_id == task.id)\
        .order_by(TaskRun.finish_time.desc())
    last_task_run = q.first()
    if last_task_run:
        task.info['last_answer'] = last_task_run.info
        # TODO: As discussed in GitHub #53
        # it is necessary to create a lock in the task!
    return task


def get_candidate_task_ids(project_id, user_id=None, user_ip=None,
                           external_uid=None, limit=1, offset=0):
    """Get all available tasks for a given project and user."""
    rows = None
    data = None
    if user_id and not user_ip and not external_uid:
        query = text('''
                     SELECT id FROM task WHERE NOT EXISTS
                     (SELECT task_id FROM task_run WHERE
                     project_id=:project_id AND user_id=:user_id
                        AND task_id=task.id)
                     AND project_id=:project_id AND state !='completed'
                     ORDER BY priority_0 DESC, id ASC LIMIT :limit OFFSET :offset''')
        rows = session.execute(query, dict(project_id=project_id,
                                           user_id=user_id, limit=limit, offset=offset))
        data = [t.id for t in rows]
    else:
        if not user_ip:
            user_ip = '127.0.0.1'
        if user_ip and not external_uid:
            query = text('''
                         SELECT id FROM task WHERE NOT EXISTS
                         (SELECT task_id FROM task_run WHERE
                         project_id=:project_id AND user_ip=:user_ip
                            AND task_id=task.id)
                         AND project_id=:project_id AND state !='completed'
                         ORDER BY priority_0 DESC, id ASC LIMIT :limit OFFSET :offset''')
            rows = session.execute(query, dict(project_id=project_id,
                                               user_ip=user_ip, limit=limit, 
                                               offset=offset))
            data = [t.id for t in rows]
        else:
            query = text('''
                         SELECT id FROM task WHERE NOT EXISTS
                         (SELECT task_id FROM task_run WHERE
                         project_id=:project_id AND external_uid=:external_uid
                            AND task_id=task.id)
                         AND project_id=:project_id AND state !='completed'
                         ORDER BY priority_0 DESC, id ASC LIMIT :limit OFFSET :offset''')
            rows = session.execute(query, dict(project_id=project_id,
                                               external_uid=external_uid,
                                               limit=limit, offset=offset))
            data = [t.id for t in rows]
    return data


def sched_variants():
    return [('default', 'Default'), ('breadth_first', 'Breadth First'),
            ('depth_first', 'Depth First')]
