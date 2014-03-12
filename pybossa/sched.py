# -*- coding: utf-8 -*-
# This file is part of PyBossa.
#
# Copyright (C) 2013 SF Isle of Man Limited
#
# PyBossa is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# PyBossa is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with PyBossa.  If not, see <http://www.gnu.org/licenses/>.

#import json
#from flask import Blueprint, request, url_for, flash, redirect, abort
#from flask import abort, request, make_response, current_app
from sqlalchemy.sql import text
import pybossa.model as model
from pybossa.core import db
import random


def new_task(app_id, user_id=None, user_ip=None, offset=0):
    '''Get a new task by calling the appropriate scheduler function.
    '''
    app = db.session.query(model.App).get(app_id)
    if not app.allow_anonymous_contributors and user_id is None:
        error = model.Task(info=dict(error="This application does not allow anonymous contributors"))
        return error
    else:
        sched_map = {
            'default': get_depth_first_task,
            'breadth_first': get_breadth_first_task,
            'depth_first': get_depth_first_task,
            'random': get_random_task,
            'incremental': get_incremental_task}
        sched = sched_map.get(app.info.get('sched'), sched_map['default'])
        return sched(app_id, user_id, user_ip, offset=offset)


def get_breadth_first_task(app_id, user_id=None, user_ip=None, n_answers=30, offset=0):
    """Gets a new task which have the least number of task runs (excluding the
    current user).

    Note that it **ignores** the number of answers limit for efficiency reasons
    (this is not a big issue as all it means is that you may end up with some
    tasks run more than is strictly needed!)
    """
    # Uncomment the next three lines to profile the sched function
    #import timeit
    #T = timeit.Timer(lambda: get_candidate_tasks(app_id, user_id,
    #                  user_ip, n_answers))
    #print "First algorithm: %s" % T.timeit(number=1)

    if user_id and not user_ip:
        sql = text('''
                   SELECT task.id, COUNT(task_run.task_id) AS taskcount FROM task
                   LEFT JOIN task_run ON (task.id = task_run.task_id) WHERE NOT EXISTS
                   (SELECT 1 FROM task_run WHERE app_id=:app_id AND
                   user_id=:user_id AND task_id=task.id)
                   AND task.app_id=:app_id AND task.state !='completed'
                   group by task.id ORDER BY taskcount, id ASC LIMIT 10;
                   ''')
        tasks = db.engine.execute(sql, app_id=app_id, user_id=user_id)
    else:
        if not user_ip: # pragma: no cover
            user_ip = '127.0.0.1'
        sql = text('''
                   SELECT task.id, COUNT(task_run.task_id) AS taskcount FROM task
                   LEFT JOIN task_run ON (task.id = task_run.task_id) WHERE NOT EXISTS
                   (SELECT 1 FROM task_run WHERE app_id=:app_id AND
                   user_ip=:user_ip AND task_id=task.id)
                   AND task.app_id=:app_id AND task.state !='completed'
                   group by task.id ORDER BY taskcount, id ASC LIMIT 10;
                   ''')

        # results will be list of (taskid, count)
        tasks = db.engine.execute(sql, app_id=app_id, user_ip=user_ip)
    # ignore n_answers for the present - we will just keep going once we've
    # done as many as we need
    tasks = [x[0] for x in tasks]
    if tasks:
        if (offset == 0):
            return db.session.query(model.Task).get(tasks[0])
        else:
            if (offset < len(tasks)):
                return db.session.query(model.Task).get(tasks[offset])
            else:
                return None
    else: # pragma: no cover
        return None


def get_depth_first_task(app_id, user_id=None, user_ip=None, n_answers=30, offset=0):
    """Gets a new task for a given application"""
    # Uncomment the next three lines to profile the sched function
    #import timeit
    #T = timeit.Timer(lambda: get_candidate_tasks(app_id, user_id,
    #                  user_ip, n_answers))
    #print "First algorithm: %s" % T.timeit(number=1)
    candidate_tasks = get_candidate_tasks(app_id, user_id, user_ip, n_answers, offset=offset)
    total_remaining = len(candidate_tasks)
    #print "Available tasks %s " % total_remaining
    if total_remaining == 0:
        return None
    if (offset == 0):
        return candidate_tasks[0]
    else:
        if (offset < len(candidate_tasks)):
            return candidate_tasks[offset]
        else:
            return None


def get_random_task(app_id, user_id=None, user_ip=None, n_answers=30, offset=0):
    """Returns a random task for the user"""
    app = db.session.query(model.App).get(app_id)
    from random import choice
    if len(app.tasks) > 0:
        return choice(app.tasks)
    else:
        return None


def get_incremental_task(app_id, user_id=None, user_ip=None, n_answers=30, offset=0):
    """Get a new task for a given application with its last given answer.
       It is an important strategy when dealing with large tasks, as
       transcriptions"""
    candidate_tasks = get_candidate_tasks(app_id, user_id, user_ip, n_answers, offset=0)
    total_remaining = len(candidate_tasks)
    if total_remaining == 0:
        return None
    rand = random.randrange(0, total_remaining)
    task = candidate_tasks[rand]
    #Find last answer for the task
    q = db.session.query(model.TaskRun)\
          .filter(model.TaskRun.task_id == task.id)\
          .order_by(model.TaskRun.finish_time.desc())
    last_task_run = q.first()
    if last_task_run:
        task.info['last_answer'] = last_task_run.info
        #TODO: As discussed in GitHub #53
        # it is necessary to create a lock in the task!
    return task


def get_candidate_tasks(app_id, user_id=None, user_ip=None, n_answers=30, offset=0):
    """Gets all available tasks for a given application and user"""
    rows = None
    if user_id and not user_ip:
        query = text('''
                     SELECT id
                     FROM task
                     WHERE
                       NOT EXISTS (SELECT task_id FROM task_run WHERE
                                   app_id=:app_id AND task_id=task.id AND user_id=:user_id)
                       AND task_runs_nr < n_answers
                       AND app_id=:app_id
                       AND state !='completed'
                     ORDER BY priority_0 DESC, id ASC
                     LIMIT 10''')
        rows = db.engine.execute(query, app_id=app_id, user_id=user_id)
    else:
        if not user_ip:
            user_ip = '127.0.0.1'
        query = text('''
                     SELECT id
                     FROM task
                     WHERE
                       NOT EXISTS (SELECT task_id FROM task_run WHERE
                                   app_id=:app_id AND task_id=task.id AND user_ip=:user_ip)
                       AND task_runs_nr < n_answers
                       AND app_id=:app_id AND state !='completed'
                     ORDER BY priority_0 DESC, id ASC
                     LIMIT 10''')
        rows = db.engine.execute(query, app_id=app_id, user_ip=user_ip)

    tasks = []
    for t in rows:
        tasks.append(db.session.query(model.Task).get(t.id))

    return tasks
