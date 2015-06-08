# -*- coding: utf8 -*-
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

from datetime import datetime
from sqlalchemy import Integer, Text
from sqlalchemy.schema import Column, ForeignKey
from sqlalchemy import event
from rq import Queue

from pybossa.core import db, sentinel
from pybossa.model import DomainObject, JSONType, make_timestamp, update_redis, \
    update_project_timestamp, webhook


webhook_queue = Queue('high', connection=sentinel.master)


class TaskRun(db.Model, DomainObject):
    '''A run of a given task by a specific user.
    '''
    __tablename__ = 'task_run'

    #: ID of the TaskRun
    id = Column(Integer, primary_key=True)
    #: UTC timestamp for when TaskRun is created.
    created = Column(Text, default=make_timestamp)
    #: Project.id of the project associated with this TaskRun.
    project_id = Column(Integer, ForeignKey('project.id'), nullable=False)
    #: Task.id of the task associated with this TaskRun.
    task_id = Column(Integer, ForeignKey('task.id', ondelete='CASCADE'),
                     nullable=False)
    #: User.id of the user contributing the TaskRun (only if authenticated)
    user_id = Column(Integer, ForeignKey('user.id'))
    #: User.ip of the user contributing the TaskRun (only if anonymous)
    user_ip = Column(Text)
    finish_time = Column(Text, default=make_timestamp)
    timeout = Column(Integer)
    calibration = Column(Integer)
    #: Value of the answer.
    info = Column(JSONType, default=dict)
    '''General writable field that should be used by clients to record results\
    of a TaskRun. Usually a template for this will be provided by Task
    For example::
        result: {
            whatever information should be recorded -- up to task presenter
        }
    '''


@event.listens_for(TaskRun, 'after_insert')
def update_task_state(mapper, conn, target):
    """Update the task.state when n_answers condition is met."""
    # Get project details
    sql_query = ('select name, short_name, webhook, info from project \
                 where id=%s') % target.project_id
    results = conn.execute(sql_query)
    project_obj = dict(id=target.project_id,
                   name=None,
                   short_name=None,
                   info=None,
                   webhook=None,
                   action_updated='TaskCompleted')
    for r in results:
        project_obj['name'] = r.name
        project_obj['short_name'] = r.short_name
        project_obj['info'] = r.info
        project_obj['webhook'] = r.webhook

    # Check if user is Authenticated
    if target.user_id is not None:
        sql_query = ('select fullname, name, info from "user" \
                     where id=%s') % target.user_id
        results = conn.execute(sql_query)
        for r in results:
            obj = dict(id=target.user_id,
                       name=r.name,
                       fullname=r.fullname,
                       info=r.info,
                       project_name=project_obj['name'],
                       project_short_name=project_obj['short_name'],
                       action_updated='UserContribution')
        # Add the event
        update_redis(obj)
    # Check if Task.state should be updated
    sql_query = ('select count(id) from task_run \
                 where task_run.task_id=%s') % target.task_id
    n_answers = conn.scalar(sql_query)
    sql_query = ('select n_answers from task \
                 where task.id=%s') % target.task_id
    task_n_answers = conn.scalar(sql_query)
    if (n_answers) >= task_n_answers:
        sql_query = ("UPDATE task SET state=\'completed\' \
                     where id=%s") % target.task_id
        conn.execute(sql_query)
        update_redis(project_obj)
        # PUSH changes via the webhook
        if project_obj['webhook']:
            payload = dict(event="task_completed",
                           project_short_name=project_obj['short_name'],
                           project_id=target.project_id,
                           task_id=target.task_id,
                           fired_at=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"))
            webhook_queue.enqueue(webhook, project_obj['webhook'], payload)



@event.listens_for(TaskRun, 'after_insert')
@event.listens_for(TaskRun, 'after_update')
def update_project(mapper, conn, target):
    """Update project updated timestamp."""
    update_project_timestamp(mapper, conn, target)
