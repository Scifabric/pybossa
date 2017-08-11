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
from sqlalchemy.sql import func, desc, text
from pybossa.model import DomainObject
from pybossa.model.task import Task
from pybossa.model.task_run import TaskRun
from pybossa.model.counter import Counter
from pybossa.core import db, sentinel, project_repo
from redis_lock import LockManager, get_active_user_count, register_active_user
from contributions_guard import ContributionsGuard
from werkzeug.exceptions import BadRequest
import random
from pybossa.cache import users as cached_users
from flask import current_app

session = db.slave_session

DEFAULT_SCHEDULER = 'locked_scheduler'

def new_task(project_id, sched, user_id=None, user_ip=None,
             external_uid=None, offset=0, limit=1, orderby='priority_0', desc=True):
    """Get a new task by calling the appropriate scheduler function."""
    sched_map = {
        'default': get_locked_task,
        'breadth_first': get_breadth_first_task,
        'depth_first': get_depth_first_task,
        'locked_scheduler': get_locked_task,
        'incremental': get_incremental_task,
        'user_pref_scheduler': get_user_pref_task}
    scheduler = sched_map.get(sched, sched_map['default'])
    return scheduler(project_id, user_id, user_ip, external_uid, offset=offset, limit=limit, orderby=orderby, desc=desc)


def can_post(project_id, task_id, user_id):
    scheduler, timeout = get_project_scheduler_and_timeout(project_id)
    if scheduler == 'locked_scheduler' or scheduler == 'user_pref_scheduler':
        return has_lock(project_id, task_id, user_id, timeout)
    else:
        return True


def can_read_task(task, user):
    project_id = task.project_id
    scheduler, timeout = get_project_scheduler_and_timeout(project_id)
    if scheduler == 'locked_scheduler' or scheduler == 'user_pref_scheduler':
        return has_read_access(user) or has_lock(project_id, task.id, user.id,
                                                 timeout)
    else:
        return True


def after_save(project_id, task_id, user_id):
    scheduler, timeout = get_project_scheduler_and_timeout(project_id)
    if scheduler == 'locked_scheduler' or scheduler == 'user_pref_scheduler':
        release_lock(project_id, task_id, user_id, timeout)


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
                   .order_by('n_task_runs ASC')\

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
                           orderby='priority_0', desc=True):
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
    query = _set_orderby_desc(query, orderby, desc)
    data = query.limit(limit).offset(offset).all()
    return _handle_tuples(data)


def get_locked_task(project_id, user_id=None, user_ip=None,
                    external_uid=None, limit=1, offset=0,
                    orderby='priority_0', desc=True):
    """ Select a new task to be returned to the contributor.

    For each incomplete task, check if the number of users working on the task
    is smaller than the number of answers still needed. In that case, acquire
    a lock on the task and return the task to the user. If offset is nonzero,
    skip that amount of available tasks before returning to the user.
    """
    if offset > 2:
        raise BadRequest()
    if offset == 1:
        return None
    user_count = get_active_user_count(project_id, sentinel.slave)

    current_app.logger.info("Number of current users: {}".format(user_count))
    sql = text('''
           SELECT task.id, COUNT(task_run.task_id) AS taskcount, n_answers,
              (SELECT info->'timeout'
               FROM project
               WHERE id=:project_id) as timeout
           FROM task
           LEFT JOIN task_run ON (task.id = task_run.task_id)
           WHERE NOT EXISTS
           (SELECT 1 FROM task_run WHERE project_id=:project_id AND
           user_id=:user_id AND task_id=task.id)
           AND task.project_id=:project_id AND task.state !='completed'
           group by task.id HAVING COUNT(task_run.task_id) < n_answers
           ORDER BY priority_0 DESC, id ASC LIMIT :limit;
           ''')

    rows = session.execute(sql, dict(project_id=project_id,
                                     user_id=user_id,
                                     limit=user_count + 5))

    for task_id, taskcount, n_answers, timeout in rows:
        timeout = timeout or TIMEOUT
        remaining = n_answers - taskcount
        if acquire_lock(project_id, task_id, user_id, remaining, timeout):
            rows.close()
            register_active_user(project_id, user_id, sentinel.master, ttl=timeout)
            return [session.query(Task).get(task_id)]

    return []


def get_user_pref_task(project_id, user_id=None, user_ip=None,
                    external_uid=None, offset=0):
    """ Select a new task based on user preference set under user profile.

    For each incomplete task, check if the number of users working on the task
    is smaller than the number of answers still needed. In that case, acquire
    a lock on the task that matches user preference(if any) with users profile
    and return the task to the user. If offset is nonzero, skip that amount of
    available tasks before returning to the user.
    """
    if offset > 2:
        raise BadRequest()
    if offset == 1:
        return None

    user_count = get_active_user_count(project_id, sentinel.slave)

    user_pref_list = cached_users.get_user_preferences(user_id)
    if user_pref_list is None:
        sql = '''
               SELECT task.id, COUNT(task_run.task_id) AS taskcount, n_answers,
                  (SELECT info->'timeout'
                   FROM project
                   WHERE id=:project_id) as timeout
               FROM task
               LEFT JOIN task_run ON (task.id = task_run.task_id)
               WHERE NOT EXISTS
               (SELECT 1 FROM task_run WHERE project_id=:project_id AND
               user_id=:user_id AND task_id=task.id)
               AND task.project_id=:project_id
               AND (task.user_pref IS NULL OR task.user_pref = '{0}')
               AND task.state !='completed'
               group by task.id ORDER BY priority_0 DESC, id ASC
               LIMIT :limit; '''.format('{}')
    else:
        sql = '''
               SELECT task.id, COUNT(task_run.task_id) AS taskcount, n_answers,
                  (SELECT info->'timeout'
                   FROM project
                   WHERE id=:project_id) as timeout
               FROM task
               LEFT JOIN task_run ON (task.id = task_run.task_id)
               WHERE NOT EXISTS
               (SELECT 1 FROM task_run WHERE project_id=:project_id AND
               user_id=:user_id AND task_id=task.id)
               AND task.project_id=:project_id
               AND (task.user_pref @> {0})
               AND task.state !='completed'
               group by task.id ORDER BY priority_0 DESC, id ASC
               LIMIT :limit; '''.format(user_pref_list)
    sqltext = text(sql)
    try:
        rows = session.execute(sqltext, dict(project_id=project_id, user_id=user_id, limit=user_count + 5))
    except Exception as e:
        current_app.logger.exception('Exception in get_user_pref_task {0}, sql: {1}'.format(str(e), str(sqltext)))
        return None

    for task_id, taskcount, n_answers, timeout in rows:
        timeout = timeout or TIMEOUT
        remaining = n_answers - taskcount
        if acquire_lock(project_id, task_id, user_id, remaining, timeout):
            rows.close()
            register_active_user(project_id, user_id, sentinel.master, ttl=timeout)
            return [session.query(Task).get(task_id)]
    return None


KEY_PREFIX = 'pybossa:project:task_requested:timestamps:{0}:{1}'
TIMEOUT = ContributionsGuard.STAMP_TTL


def has_lock(project_id, task_id, user_id, timeout):
    lock_manager = LockManager(sentinel.master, timeout)
    key = get_key(project_id, task_id)
    return lock_manager.has_lock(key, user_id)


def acquire_lock(project_id, task_id, user_id, limit, timeout):
    lock_manager = LockManager(sentinel.master, timeout)
    key = get_key(project_id, task_id)
    return lock_manager.acquire_lock(key, user_id, limit)


def release_lock(project_id, task_id, user_id, timeout):
    lock_manager = LockManager(sentinel.master, timeout)
    key = get_key(project_id, task_id)
    lock_manager.release_lock(key, user_id)


def get_key(project_id, task_id):
    return KEY_PREFIX.format(project_id, task_id)


def get_project_scheduler_and_timeout(project_id):
    project = project_repo.get(project_id)
    scheduler = project.info.get('sched', 'default')
    timeout = project.info.get('timeout', TIMEOUT)
    if scheduler == 'default':
        scheduler = DEFAULT_SCHEDULER
    return scheduler, timeout


def has_read_access(user):
    return not user.is_anonymous() and (user.admin or user.subadmin)


def sched_variants():
    return [('default', 'Default'), ('breadth_first', 'Breadth First'),
            ('depth_first', 'Depth First'),
            ('locked_scheduler', 'Locked'),
            ('user_pref_scheduler', 'User Preference Scheduler')]


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
