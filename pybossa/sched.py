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
from sqlalchemy.sql import func, desc, text
from sqlalchemy.sql import and_, or_
from pybossa.model import DomainObject
from pybossa.model.task import Task
from pybossa.model.task_run import TaskRun
from pybossa.model.counter import Counter
from pybossa.core import db, sentinel, project_repo, task_repo
from redis_lock import LockManager, get_active_user_count, register_active_user
from contributions_guard import ContributionsGuard
from werkzeug.exceptions import BadRequest, Forbidden
import random
from pybossa.cache import users as cached_users
from flask import current_app
from pybossa import data_access
from datetime import datetime
#TODO: Can this be removed? It's a duplicate.
from flask import current_app


session = db.slave_session


class Schedulers(object):

    locked = 'locked_scheduler'
    user_pref = 'user_pref_scheduler'


DEFAULT_SCHEDULER = Schedulers.locked
TIMEOUT = ContributionsGuard.STAMP_TTL


def new_task(project_id, sched, user_id=None, user_ip=None,
             external_uid=None, offset=0, limit=1, orderby='priority_0',
             desc=True, rand_within_priority=False,
             gold_only=False):
    """Get a new task by calling the appropriate scheduler function."""
    sched_map = {
        'default': get_locked_task,
        'breadth_first': get_breadth_first_task,
        'depth_first': get_depth_first_task,
        Schedulers.locked: get_locked_task,
        'incremental': get_incremental_task,
        Schedulers.user_pref: get_user_pref_task,
        'depth_first_all': get_depth_first_all_task
    }
    scheduler = sched_map.get(sched, sched_map['default'])

    project = project_repo.get(project_id)
    # This is here for testing. It removes the random variable to make testing deterministic.
    disable_gold = not project.info.get('enable_gold', True)
    present_gold_task = False if gold_only or disable_gold else not random.randint(0, 10)
    return scheduler(
        project_id,
        user_id,
        user_ip,
        external_uid,
        offset=offset,
        limit=limit,
        orderby=orderby,
        desc=desc,
        rand_within_priority=rand_within_priority,
        present_gold_task=present_gold_task,
        gold_only=gold_only
    )


def is_locking_scheduler(sched):
    return sched in [Schedulers.locked, Schedulers.user_pref, 'default']


def can_read_task(task, user):
    project_id = task.project_id
    scheduler, timeout = get_project_scheduler_and_timeout(project_id)
    if is_locking_scheduler(scheduler):
        return has_read_access(user) or has_lock(task.id, user.id,
                                                 timeout)
    else:
        return True


def can_post(project_id, task_id, user_id_or_ip):
    scheduler = get_project_scheduler(project_id, session)
    if is_locking_scheduler(scheduler):
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
    if is_locking_scheduler(scheduler):
        release_lock(task_run.task_id, uid, TIMEOUT)


def get_breadth_first_task(project_id, user_id=None, user_ip=None,
                           external_uid=None, offset=0, limit=1, orderby='id',
                           desc=False, **kwargs):
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
                   .filter(or_(Task.expiration == None, Task.expiration > datetime.utcnow()))\
                   .group_by(Task.id)\
                   .order_by('n_task_runs ASC')\

    query = _set_orderby_desc(query, orderby, desc)
    data = query.limit(limit).offset(offset).all()
    return _handle_tuples(data)


def get_depth_first_task(project_id, user_id=None, user_ip=None,
                         external_uid=None, offset=0, limit=1,
                         orderby='priority_0', desc=True, **kwargs):
    """Get a new task for a given project."""
    tasks = get_candidate_task_ids(project_id, user_id,
                                   user_ip, external_uid, limit, offset,
                                   orderby=orderby, desc=desc)
    return tasks


def get_depth_first_all_task(project_id, user_id=None, user_ip=None,
                             external_uid=None, offset=0, limit=1,
                             orderby='priority_0', desc=True, **kwargs):
    """Get a new task for a given project."""
    tasks = get_candidate_task_ids(project_id, user_id,
                                   user_ip, external_uid, limit, offset,
                                   orderby=orderby, desc=desc, completed=False)
    return tasks


def get_incremental_task(project_id, user_id=None, user_ip=None,
                         external_uid=None, offset=0, limit=1, orderby='id',
                         desc=False, **kwargs):
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

    query = session.query(Task)\
                   .filter(and_(~Task.id.in_(subquery.subquery()),
                                            Task.project_id == project_id,
                                            Task.state != 'completed'))\
                   .filter(or_(Task.expiration == None, Task.expiration > datetime.utcnow()))

    if completed is False:
        query = session.query(Task).filter(and_(~Task.id.in_(subquery.subquery()),
                                                Task.project_id == project_id))

    query = _set_orderby_desc(query, orderby, desc)
    data = query.limit(limit).offset(offset).all()
    return _handle_tuples(data)


def locked_scheduler(query_factory):
    @wraps(query_factory)
    def template_get_locked_task(project_id, user_id=None, user_ip=None,
                                 external_uid=None, limit=1, offset=0,
                                 orderby='priority_0', desc=True,
                                 rand_within_priority=False,
                                 present_gold_task=False,
                                 gold_only=False):
        if offset > 2:
            raise BadRequest('')
        if offset > 0:
            return None
        task_id, lock_seconds = get_task_id_and_duration_for_project_user(project_id, user_id)
        if lock_seconds > 10:
            task = session.query(Task).get(task_id)
            if task:
                return [task]
        user_count = get_active_user_count(project_id, sentinel.master)
        current_app.logger.info(
            "Project {} - number of current users: {}"
            .format(project_id, user_count))

        sql = query_factory(
            project_id,
            user_id=user_id,
            user_ip=user_ip,
            external_uid=external_uid,
            limit=limit,
            offset=offset,
            orderby=orderby,
            desc=desc,
            rand_within_priority=rand_within_priority,
            present_gold_task=present_gold_task,
            gold_only=gold_only
        )
        rows = session.execute(sql, dict(project_id=project_id,
                                         user_id=user_id,
                                         limit=user_count + 5))

        for task_id, taskcount, n_answers, calibration, timeout in rows:
            timeout = timeout or TIMEOUT
            remaining = float('inf') if calibration else n_answers - taskcount
            if acquire_lock(task_id, user_id, remaining, timeout):
                rows.close()
                save_task_id_project_id(task_id, project_id, 2 * timeout)
                register_active_user(project_id, user_id, sentinel.master, ttl=timeout)

                task_type = 'gold task' if calibration else 'task'
                current_app.logger.info(
                    'Project {} - user {} obtained {} {}, timeout: {}'
                    .format(project_id, user_id, task_type, task_id, timeout))
                return [session.query(Task).get(task_id)]

        return []

    return template_get_locked_task


@locked_scheduler
def get_locked_task(
    project_id,
    user_id=None,
    user_ip=None,
    external_uid=None,
    offset=0,
    limit=1,
    orderby='priority_0',
    desc=True,
    rand_within_priority=False,
    present_gold_task=False,
    gold_only=False
):
    having_clause = 'HAVING COUNT(task_run.task_id) < n_answers' if not (present_gold_task or gold_only) else ''
    allowed_task_levels_clause = data_access.get_data_access_db_clause_for_task_assignment(user_id)
    order_by_calib = 'DESC NULLS LAST' if present_gold_task else ''
    gold_only_clause = 'AND task.calibration = 1' if gold_only else ''

    sql = '''
           SELECT task.id, COUNT(task_run.task_id) AS taskcount, n_answers, task.calibration,
              (SELECT info->'timeout'
               FROM project
               WHERE id=:project_id) as timeout
           FROM task
           LEFT JOIN task_run ON (task.id = task_run.task_id)
           WHERE NOT EXISTS
           (SELECT 1 FROM task_run WHERE project_id=:project_id AND
           user_id=:user_id AND task_id=task.id)
           AND task.project_id=:project_id
           AND ((task.expiration IS NULL) OR (task.expiration > (now() at time zone 'utc')::timestamp))
           AND task.state !='completed'
           {}
           {}
           group by task.id
           {}
           ORDER BY task.calibration {}, priority_0 DESC, {} LIMIT :limit;
           '''.format(
                allowed_task_levels_clause,
                gold_only_clause,
                having_clause,
                order_by_calib,
                'random()' if rand_within_priority else 'id ASC'
            )
    return text(sql)


@locked_scheduler
def get_user_pref_task(
    project_id,
    user_id=None,
    user_ip=None,
    external_uid=None,
    limit=1,
    offset=0,
    orderby='priority_0',
    desc=True,
    rand_within_priority=False,
    present_gold_task=False,
    gold_only=False
):
    """ Select a new task based on user preference set under user profile.

    For each incomplete task, check if the number of users working on the task
    is smaller than the number of answers still needed. In that case, acquire
    a lock on the task that matches user preference(if any) with users profile
    and return the task to the user. If offset is nonzero, skip that amount of
    available tasks before returning to the user.
    """

    user_pref_list = cached_users.get_user_preferences(user_id)
    secondary_order = 'random()' if rand_within_priority else 'id ASC'
    allowed_task_levels_clause = data_access.get_data_access_db_clause_for_task_assignment(user_id)
    order_by_calib = 'DESC NULLS LAST' if present_gold_task else ''
    gold_only_clause = 'AND task.calibration = 1' if gold_only else ''

    sql = '''
           SELECT task.id, COUNT(task_run.task_id) AS taskcount, n_answers, task.calibration,
              (SELECT info->'timeout'
               FROM project
               WHERE id=:project_id) as timeout
           FROM task
           LEFT JOIN task_run ON (task.id = task_run.task_id)
           WHERE NOT EXISTS
           (SELECT 1 FROM task_run WHERE project_id=:project_id AND
           user_id=:user_id AND task_id=task.id)
           AND task.project_id=:project_id
           AND ({})
           AND ((task.expiration IS NULL) OR (task.expiration > (now() at time zone 'utc')::timestamp))
           AND task.state !='completed'
           {}
           {}
           group by task.id
           ORDER BY task.calibration {}, priority_0 DESC,
           {}
           LIMIT :limit;
           '''.format(
                user_pref_list,
                allowed_task_levels_clause,
                gold_only_clause,
                order_by_calib,
                secondary_order
            )
    return text(sql)


TASK_USERS_KEY_PREFIX = 'pybossa:project:task_requested:timestamps:{0}'
USER_TASKS_KEY_PREFIX = 'pybossa:user:task_acquired:timestamps:{0}'
TASK_ID_PROJECT_ID_KEY_PREFIX = 'pybossa:task_id:project_id:{0}'
TIMEOUT = ContributionsGuard.STAMP_TTL


def has_lock(task_id, user_id, timeout):
    lock_manager = LockManager(sentinel.master, timeout)
    task_users_key = get_task_users_key(task_id)
    return lock_manager.has_lock(task_users_key, user_id)


def acquire_lock(task_id, user_id, limit, timeout, pipeline=None, execute=True):
    redis_conn = sentinel.master
    pipeline = pipeline or redis_conn.pipeline(transaction=True)
    lock_manager = LockManager(redis_conn, timeout)
    task_users_key = get_task_users_key(task_id)
    user_tasks_key = get_user_tasks_key(user_id)
    if lock_manager.acquire_lock(task_users_key, user_id, limit, pipeline=pipeline):
        lock_manager.acquire_lock(user_tasks_key, task_id, float('inf'), pipeline=pipeline)
        if execute:
            return all(not isinstance(r, Exception) for r in pipeline.execute())
        return True
    return False


def release_user_locks_for_project(user_id, project_id):
    user_tasks = get_user_tasks(user_id, TIMEOUT)
    user_task_ids = user_tasks.keys()
    results = get_task_ids_project_id(user_task_ids)
    task_ids = []
    for task_id, task_project_id in zip(user_task_ids, results):
        if not task_project_id:
            task_project_id = task_repo.get_task(task_id).project_id
        if int(task_project_id) == project_id:
            release_lock(task_id, user_id, TIMEOUT)
            task_ids.append(task_id)
    current_app.logger.info('released user id {} locks on tasks {}'.format(user_id, task_ids))
    return task_ids


def release_lock(task_id, user_id, timeout, pipeline=None, execute=True):
    redis_conn = sentinel.master
    pipeline = pipeline or redis_conn.pipeline(transaction=True)
    lock_manager = LockManager(redis_conn, timeout)
    task_users_key = get_task_users_key(task_id)
    user_tasks_key = get_user_tasks_key(user_id)
    lock_manager.release_lock(task_users_key, user_id, pipeline=pipeline)
    lock_manager.release_lock(user_tasks_key, task_id, pipeline=pipeline)
    if execute:
        pipeline.execute()


def get_locks(task_id, timeout):
    lock_manager = LockManager(sentinel.master, timeout)
    task_users_key = get_task_users_key(task_id)
    return lock_manager.get_locks(task_users_key)


def get_user_tasks(user_id, timeout):
    lock_manager = LockManager(sentinel.master, timeout)
    user_tasks_key = get_user_tasks_key(user_id)
    return lock_manager.get_locks(user_tasks_key)


def save_task_id_project_id(task_id, project_id, timeout):
    task_id_project_id_key = get_task_id_project_id_key(task_id)
    sentinel.master.setex(task_id_project_id_key, timeout, project_id)


def get_task_ids_project_id(task_ids):
    keys = [get_task_id_project_id_key(t) for t in task_ids]
    if keys:
        return sentinel.master.mget(keys)
    return []


def get_task_users_key(task_id):
    return TASK_USERS_KEY_PREFIX.format(task_id)


def get_user_tasks_key(user_id):
    return USER_TASKS_KEY_PREFIX.format(user_id)


def get_task_id_project_id_key(task_id):
    return TASK_ID_PROJECT_ID_KEY_PREFIX.format(task_id)


def get_task_id_and_duration_for_project_user(project_id, user_id):
    user_tasks = get_user_tasks(user_id, TIMEOUT)
    user_task_ids = user_tasks.keys()
    results = get_task_ids_project_id(user_task_ids)
    max_seconds_task_id = -1
    max_seconds_remaining = float('-inf')
    for task_id, task_project_id in zip(user_task_ids, results):
        if not task_project_id:
            task_project_id = task_repo.get_task(task_id).project_id
            save_task_id_project_id(task_id, task_project_id, 2 * TIMEOUT)
        if int(task_project_id) == project_id:
            seconds_remaining = LockManager.seconds_remaining(user_tasks[task_id])
            if seconds_remaining > max_seconds_remaining:
                max_seconds_task_id = int(task_id)
                max_seconds_remaining = seconds_remaining
    if max_seconds_task_id > 0:
        return max_seconds_task_id, max_seconds_remaining
    return None, -1


def release_user_locks(user_id):
    redis_conn = sentinel.master
    pipeline = redis_conn.pipeline(transaction=True)
    for key in get_user_tasks(user_id, TIMEOUT).keys():
        release_lock(key, user_id, TIMEOUT, pipeline=pipeline, execute=False)
    pipeline.execute()


def get_project_scheduler_and_timeout(project_id):
    project = project_repo.get(project_id)
    if not project:
        raise Forbidden('Invalid project_id')
    return get_scheduler_and_timeout(project)


def get_scheduler_and_timeout(project):
    scheduler = project.info.get('sched', 'default')
    timeout = project.info.get('timeout', TIMEOUT)
    if scheduler == 'default':
        scheduler = DEFAULT_SCHEDULER
    return scheduler, timeout


def has_read_access(user):
    return not user.is_anonymous and (user.admin or user.subadmin)


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
            (Schedulers.locked, 'Locked'),
            (Schedulers.user_pref, 'User Preference Scheduler'),
            ('depth_first_all', 'Depth First All')
            ]


def randomizable_scheds():
    scheds = [Schedulers.locked, Schedulers.user_pref]
    if DEFAULT_SCHEDULER in scheds:
        scheds.append('default')
    return scheds


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
