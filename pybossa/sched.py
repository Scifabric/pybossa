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
from functools import wraps
from werkzeug.exceptions import Forbidden, BadRequest
from sqlalchemy.sql import func, desc, text
from sqlalchemy import and_
from pybossa.model import DomainObject
from pybossa.model.task import Task
from pybossa.model.task_run import TaskRun
from pybossa.model.counter import Counter
from pybossa.core import db, sentinel, project_repo
from pybossa.contributions_guard import ContributionsGuard
from pybossa.redis_lock import (LockManager, get_active_user_count,
    register_active_user)
import random

from flask import current_app


session = db.slave_session


TIMEOUT = ContributionsGuard.STAMP_TTL


def new_task(project_id, sched, user_id=None, user_ip=None,
             external_uid=None, offset=0, limit=1, orderby='priority_0', desc=True):
    """Get a new task by calling the appropriate scheduler function."""
    sched_map = {
        'default': get_depth_first_task,
        'breadth_first': get_breadth_first_task,
        'depth_first': get_depth_first_task,
        'incremental': get_incremental_task,
        'depth_first_all': get_depth_first_all_task,
        'locked': get_locked_task}
    scheduler = sched_map.get(sched, sched_map['default'])
    return scheduler(project_id, user_id, user_ip, external_uid, offset=offset, limit=limit, orderby=orderby, desc=desc)


def can_post(project_id, task_id, user_id_or_ip):
    scheduler = get_project_scheduler(project_id, session)
    if scheduler == 'locked':
        user_id = user_id_or_ip['user_id'] or \
                user_id_or_ip['external_uid'] or \
                user_id_or_ip['user_ip'] or \
                '127.0.0.1'
        allowed = has_lock(task_id, user_id, TIMEOUT)
        return allowed
    else:
        return True


def after_save(task_run, conn):
    scheduler = get_project_scheduler(task_run.project_id, conn)
    uid = task_run.user_id or \
          task_run.external_uid or \
          task_run.user_ip or \
          '127.0.0.1'
    if scheduler == 'locked':
        release_lock(task_run.task_id, uid, TIMEOUT)


def get_breadth_first_task(project_id, user_id=None, user_ip=None,
                           external_uid=None, offset=0, limit=1, orderby='id', desc=False):
    """Get a new task which have the least number of task runs."""
    project_query = session.query(Task.id).filter(Task.project_id==project_id,
                                                  Task.state!='completed')
    if user_id and not user_ip and not external_uid:
        subquery = session.query(TaskRun.task_id).filter_by(project_id=project_id,
                                                            user_id=user_id)
    else:
        if not user_ip:  # pragma: no cover
            user_ip = '127.0.0.1'
        if user_ip and not external_uid:
            subquery = session.query(TaskRun.task_id).filter_by(project_id=project_id,
                                                                user_ip=user_ip)
        else:
            subquery = session.query(TaskRun.task_id).filter_by(project_id=project_id,
                                                                external_uid=external_uid)

    tmp = project_query.except_(subquery)
    query = session.query(Task, func.sum(Counter.n_task_runs).label('n_task_runs'))\
                   .filter(Task.id==Counter.task_id)\
                   .filter(Counter.task_id.in_(tmp))\
                   .group_by(Task.id)\
                   .order_by(text('n_task_runs ASC'))\

    query = _set_orderby_desc(query, orderby, desc)
    data = query.limit(limit).offset(offset).all()
    return _handle_tuples(data)


def get_depth_first_task(project_id, user_id=None, user_ip=None,
                         external_uid=None, offset=0, limit=1,
                         orderby='priority_0', desc=True):
    """Get a new task for a given project."""
    tasks = get_candidate_task_ids(project_id, user_id,
                                   user_ip, external_uid, limit, offset,
                                   orderby=orderby, desc=desc)
    return tasks


def get_depth_first_all_task(project_id, user_id=None, user_ip=None,
                             external_uid=None, offset=0, limit=1,
                             orderby='priority_0', desc=True):
    """Get a new task for a given project."""
    tasks = get_candidate_task_ids(project_id, user_id,
                                   user_ip, external_uid, limit, offset,
                                   orderby=orderby, desc=desc, completed=False)
    return tasks


def get_incremental_task(project_id, user_id=None, user_ip=None,
                         external_uid=None, offset=0, limit=1, orderby='id', desc=False):
    """Get a new task for a given project with its last given answer.

    It is an important strategy when dealing with large tasks, as
    transcriptions.
    """
    candidate_tasks = get_candidate_task_ids(project_id, user_id, user_ip,
                                                external_uid, limit, offset,
                                                orderby='priority_0', desc=True)
    total_remaining = len(candidate_tasks)
    if total_remaining == 0:
        return None
    rand = random.randrange(0, total_remaining)
    task = candidate_tasks[rand]
    # Find last answer for the task
    q = session.query(TaskRun)\
        .filter(TaskRun.task_id == task.id)\
        .order_by(TaskRun.finish_time.desc())
    last_task_run = q.first()
    if last_task_run:
        task.info['last_answer'] = last_task_run.info
        # TODO: As discussed in GitHub #53
        # it is necessary to create a lock in the task!
    return [task]


def get_candidate_task_ids(project_id, user_id=None, user_ip=None,
                           external_uid=None, limit=1, offset=0,
                           orderby='priority_0', desc=True, completed=True):
    """Get all available tasks for a given project and user."""
    data = None
    if user_id and not user_ip and not external_uid:
        subquery = session.query(TaskRun.task_id).filter_by(project_id=project_id, user_id=user_id)
    else:
        if not user_ip:
            user_ip = '127.0.0.1'
        if user_ip and not external_uid:
            subquery = session.query(TaskRun.task_id).filter_by(project_id=project_id, user_ip=user_ip)
        else:
            subquery = session.query(TaskRun.task_id).filter_by(project_id=project_id, external_uid=external_uid)

    query = session.query(Task).filter(and_(~Task.id.in_(subquery.subquery()),
                                            Task.project_id == project_id,
                                            Task.state != 'completed'))
    if completed is False:
        query = session.query(Task).filter(and_(~Task.id.in_(subquery.subquery()),
                                                Task.project_id == project_id))

    query = _set_orderby_desc(query, orderby, desc)
    data = query.limit(limit).offset(offset).all()
    return _handle_tuples(data)


def get_locked_task(project_id, user_id=None, user_ip=None,
                    external_uid=None, offset=0, limit=1,
                    orderby='priority_0', desc=True):
    if offset > 2:
        raise BadRequest()
    if offset == 2:
        return []

    user_count = get_active_user_count(project_id, sentinel.master)
    limit = 2*user_count

    user_param = 'user_id'
    uid = user_id
    if not user_id:
        if not user_ip:
            user_ip = '127.0.0.1'
        if not external_uid:
            user_param = 'user_ip'
            uid = user_ip
        else:
            user_param = 'external_uid'
            uid = external_uid

    sql = text('''
           SELECT task.id, COUNT(task_run.task_id) AS taskcount, n_answers
           FROM task
           LEFT JOIN task_run ON (task.id = task_run.task_id)
           WHERE NOT EXISTS
           (SELECT 1 FROM task_run WHERE project_id=:project_id AND
           {}=:uid AND task_id=task.id)
           AND task.project_id=:project_id AND task.state !='completed'
           group by task.id HAVING COUNT(task_run.task_id) < n_answers
           ORDER BY priority_0 DESC, id ASC LIMIT :limit;
           '''.format(user_param))

    rows = session.execute(sql, dict(project_id=project_id,
                                     uid=uid, limit=limit + 5))

    for task_id, taskcount, n_answers in rows:
        remaining = n_answers - taskcount
        if acquire_lock(task_id, uid, remaining, TIMEOUT):
            if offset == 1:
                offset = 0
                continue
            rows.close()
            register_active_user(project_id, uid, sentinel.master, ttl=TIMEOUT)
            return [session.query(Task).get(task_id)]

    return []


TASK_USERS_KEY_PREFIX = 'pybossa:project:task_requested:timestamps:{0}'
TASK_ID_PROJECT_ID_KEY_PREFIX = 'pybossa:task_id:project_id:{0}'


def has_lock(task_id, user_id, timeout):
    lock_manager = LockManager(sentinel.master, timeout)
    task_users_key = get_task_users_key(task_id)
    return lock_manager.has_lock(task_users_key, user_id)


def acquire_lock(task_id, user_id, limit, timeout, pipeline=None, execute=True):
    redis_conn = sentinel.master
    pipeline = pipeline or redis_conn.pipeline(transaction=True)
    lock_manager = LockManager(redis_conn, timeout)
    task_users_key = get_task_users_key(task_id)
    if lock_manager.acquire_lock(task_users_key, user_id, limit, pipeline=pipeline):
        if execute:
            return all(not isinstance(r, Exception) for r in pipeline.execute())
        return True
    return False


def release_lock(task_id, user_id, timeout, pipeline=None, execute=True):
    redis_conn = sentinel.master
    pipeline = pipeline or redis_conn.pipeline(transaction=True)
    lock_manager = LockManager(redis_conn, timeout)
    task_users_key = get_task_users_key(task_id)
    lock_manager.release_lock(task_users_key, user_id, pipeline=pipeline)
    if execute:
        pipeline.execute()


def get_task_users_key(task_id):
    return TASK_USERS_KEY_PREFIX.format(task_id)


def get_project_scheduler(project_id, conn):
    sql = text('''
        SELECT info->>'sched' as sched FROM project WHERE id=:project_id;
        ''')
    row = conn.execute(sql, dict(project_id=project_id)).first()
    if not row:
        return 'default'
    return row.sched or 'default'


def sched_variants():
    return [('default', 'Default'), ('breadth_first', 'Breadth First'),
            ('depth_first', 'Depth First'),
            ('depth_first_all', 'Depth First All'),
            ('locked', 'Locked')
            ]


def _set_orderby_desc(query, orderby, descending):
    """Set order by to query."""
    if orderby == 'fav_user_ids':
        n_favs = func.coalesce(func.array_length(Task.fav_user_ids, 1), 0).label('n_favs')
        query = query.add_column(n_favs)
        if descending:
            query = query.order_by(desc("n_favs"))
        else:
            query = query.order_by("n_favs")
    else:
        if descending:
            query = query.order_by(getattr(Task, orderby).desc())
        else:
            query = query.order_by(getattr(Task, orderby).asc())
    #query = query.order_by(Task.id.asc())
    return query


def _handle_tuples(data):
    """Handle tuples when query returns several columns."""
    tmp = []
    for datum in data:
        if isinstance(datum, DomainObject):
            tmp.append(datum)
        else:
            tmp.append(datum[0])
    return tmp
