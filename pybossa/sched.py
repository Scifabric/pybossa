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
import pybossa.model as model
import random

def get_default_task(app_id, user_id=None, user_ip=None, n_answers=30):
    """Gets a new task for a given application"""
    # Uncomment the next three lines to profile the sched function
    #import timeit
    #T = timeit.Timer(lambda: get_candidate_tasks2(app_id, user_id, user_ip, n_answers))
    #print T.timeit(number=1)
    candidate_tasks = get_candidate_tasks(app_id, user_id, user_ip, n_answers)
    total_remaining = len(candidate_tasks)
    #print "Available tasks %s " % total_remaining
    if total_remaining == 0:
        return None
    #rand = random.randrange(0, total_remaining)
    #out = candidate_tasks[rand]
    return candidate_tasks[0]


def get_random_task(app_id, user_id=None, user_ip=None, n_answers=30):
    """Returns a random task for the user"""
    app = model.Session.query(model.App).get(app_id)
    from random import choice
    return choice(app.tasks)


def get_incremental_task(app_id, user_id=None, user_ip=None, n_answers=30):
    """Get a new task for a given application with its last given answer.
       It is an important strategy when dealing with large tasks, as 
       transcriptions"""
    candidate_tasks = get_candidate_tasks(app_id, user_id, user_ip, n_answers)
    total_remaining = len(candidate_tasks)
    print "Available tasks %s " % total_remaining
    if total_remaining == 0:
        return None
    rand = random.randrange(0, total_remaining)
    task = candidate_tasks[rand]
    #Find last answer for the task
    q = model.Session.query(model.TaskRun)\
            .filter(model.TaskRun.task_id == task.id)\
            .order_by(model.TaskRun.finish_time.desc())
    last_task_run = q.first()
    if last_task_run:
        task.info['last_answer'] = last_task_run.info
        #ToDo As discussed in GitHub #53 it is necessary to create a lock in the task!
    return task


def get_candidate_tasks(app_id, user_id=None, user_ip=None, n_answers=30):
    """Gets all available tasks for a given application and user"""
    # Get all pending tasks for the application
    offset = 0
    candidate_tasks = []
    tasks = model.Session.query(model.Task)\
            .filter(model.Task.app_id==app_id)\
            .filter(model.Task.state!="completed")\
            .limit(10)

    for t in tasks.offset(offset):
        # Check if the task is completed or not
        # DEPRECATED: t.info.n_answers will be removed
        # DEPRECATED: so if your task has a different value for n_answers
        # DEPRECATED: use t.n_answers instead
        if (t.info.get('n_answers')):
            t.n_answers = int(t.info['n_answers'])
        # NEW WAY!
        if t.n_answers == None:
            t.n_answers = 30

        if (len(t.task_runs) >= t.n_answers):
                t.state = "completed"
                model.Session.merge(t)
                model.Session.commit()
        else:
            # Check if the user has participated in this task
            if user_id and not user_ip:
                participated = model.Session.query(model.TaskRun)\
                        .filter(model.TaskRun.app_id==app_id)\
                        .filter(model.TaskRun.task_id==t.id)\
                        .filter(model.TaskRun.user_id==user_id)\
                        .count()
                # The user has not participated in this task
                if not participated:
                    candidate_tasks.append(t)
                    break
            else:
                if not user_ip:
                    user_ip = "127.0.0.1"
                participated = model.Session.query(model.TaskRun)\
                        .filter(model.TaskRun.app_id==app_id)\
                        .filter(model.TaskRun.task_id==t.id)\
                        .filter(model.TaskRun.user_ip==user_ip)\
                        .count()
                # The user has not participated in this task
                if not participated:
                    candidate_tasks.append(t)
                    break
        offset += 10
    return candidate_tasks
