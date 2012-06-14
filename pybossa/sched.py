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

def get_task(app_id, user_id=None, user_ip=None, limit=10):
    """Gets a new task for a given application"""
    #: Get all the Task and TaskRuns for this app
    q = model.Session.query(model.Task).outerjoin(model.TaskRun).filter(model.Task.app_id == app_id)

    tasks = q.all()
    # print "Available Task for this AppID: %s : %s" % (app_id, len(tasks))
    for t in tasks:
        # print "This TaskID: %s has %s TaskRuns" % (t.id,len(t.task_runs))
        if (len(t.task_runs) >= limit):
            # print "This TaskID: %s has more than %s TaskRuns" % (t.id, limit)
            q = q.filter(model.Task.id!=t.id)
            # print "Removing it from the candidate Tasks"
    # print "New Query with Tasks with less than the limit %s " % limit
    #for t in q.all():
        #print "This TaskID: %s has less than %s TaskRuns" % (t.id, limit)
    #print "There are %s Available Tasks with less TaskRuns than %s" % (len(q.all()),limit)

    #: If a user has already given an answer to a task, remove it from the fina list
    if user_id and not user_ip:
        #print "Authenticated user"
        tasks = q.filter(model.TaskRun.user_id==user_id)
    else:
        #print "Anonymous user"
        if user_ip:
            tasks = q.filter(model.TaskRun.user_ip==user_ip)
        else:
            tasks = q.filter(model.TaskRun.user_ip=="127.0.0.1")
    
    for t in tasks:
        #print "Print Removing TaskID: %s because user has already provided an answer" % t.id
        q = q.filter(model.Task.id != t.id)

    if user_id and not user_ip:
        print "This UserID: %s can answer %s Tasks" % (user_id, len(q.all()))
    else:
        print "This Anonymous User with IP: %s can answer %s Tasks" % (user_ip, len(q.all()))

    total_remaining = q.count()
    if q.count() == 0:
        return None
    rand = random.randrange(0, total_remaining)
    out = q[rand]
    return out
