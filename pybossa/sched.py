# This file is part of PyBOSSA.
#
# PyBOSSA is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# PyBOSSA is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with PyBOSSA.  If not, see <http://www.gnu.org/licenses/>.

#import json
#from flask import Blueprint, request, url_for, flash, redirect, abort
#from flask import abort, request, make_response, current_app
from sqlalchemy.sql import not_, text
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
            'incremental': get_incremental_task
            }
        sched = sched_map.get(app.info.get('sched'), sched_map['default'])
        return sched(app_id, user_id, user_ip, offset=offset)


def get_breadth_first_task(app_id, user_id=None, user_ip=None, n_answers=30, offset=0):
    """Gets a new task which have the least number of task runs (excluding the
    current user).

    Note that it **ignores** the number of answers limit for efficiency reasons
    (this is not a big issue as all it means is that you may end up with some
    tasks run more than is strictly needed!)

    NB: current algorithm has the draw-back that it will allocate tasks to a
    user which the user has already done if that task has the least number of
    performances (excluding that done by the user). To fix this is possible but
    would be costly as we'd need to find all tasks the user has done and
    exclude those task ids explicitly.
    """
    # Uncomment the next three lines to profile the sched function
    #import timeit
    #T = timeit.Timer(lambda: get_candidate_tasks(app_id, user_id,
    #                  user_ip, n_answers))
    #print "First algorithm: %s" % T.timeit(number=1)

    sql = text('''
SELECT task.id, count(task_run.task_id) AS taskcount from task
LEFT JOIN task_run ON (task.id = task_run.task_id)
WHERE task.app_id = :app_id AND
(task_run.user_id IS NULL OR task_run.user_id != :user_id OR task_run.id IS NULL)
GROUP BY task.id
ORDER BY taskcount ASC limit 10 ;
''')
    # results will be list of (taskid, count)
    tasks = db.engine.execute(sql, app_id=app_id, user_id=user_id)
    # ignore n_answers for the present - we will just keep going once we've
    # done as many as we need
    # tasks = [ x[0] for x in tasks if x[1] < n_answers ]
    tasks = [ x[0] for x in tasks ]
    print len(tasks)
    if tasks:
        if (offset==0):
            return db.session.query(model.Task).get(tasks[0])
        else:
            if (offset < len(tasks)):
                return db.session.query(model.Task).get(tasks[offset])
            else:
                return None
    else:
        return None
    # candidate_tasks = get_candidate_tasks(app_id, user_id, user_ip, n_answers)
    # total_remaining = len(candidate_tasks)
    #print "Available tasks %s " % total_remaining
    # if total_remaining == 0:
    #    return None
    # return candidate_tasks[0]


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
    return choice(app.tasks)


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

    print "Using offset = %s" % offset
    if user_id and not user_ip:
        participated_tasks = db.session.query(model.TaskRun.task_id)\
                .filter_by(user_id=user_id)\
                .filter_by(app_id=app_id)\
                .order_by(model.TaskRun.task_id)
    else:
        if not user_ip:
            user_ip = "127.0.0.1"
        participated_tasks = db.session.query(model.TaskRun.task_id)\
                .filter_by(user_ip=user_ip)\
                .filter_by(app_id=app_id)\
                .order_by(model.TaskRun.task_id)

    tasks = db.session.query(model.Task)\
            .filter(not_(model.Task.id.in_(participated_tasks.all())))\
            .filter_by(app_id=app_id)\
            .filter(model.Task.state != "completed")\
            .order_by(model.Task.id)\
            .limit(10)\
            .all()

    candidate_tasks = []

    for t in tasks:
        # DEPRECATED: t.info.n_answers will be removed
        # DEPRECATED: so if your task has a different value for n_answers
        # DEPRECATED: use t.n_answers instead
        #print t.id
        if (t.info.get('n_answers')):
            t.n_answers = int(t.info['n_answers'])
        # NEW WAY!
        if t.n_answers is None:
            t.n_answers = 30

        if (len(t.task_runs) >= t.n_answers):
                t.state = "completed"
                db.session.merge(t)
                db.session.commit()
        else:
            candidate_tasks.append(t)
            if (offset == 0):
                break
    return candidate_tasks
