# -*- coding: utf8 -*-
# This file is part of PyBossa.
#
# Copyright (C) 2015 SF Isle of Man Limited
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

from rq import Queue
from sqlalchemy import event

from pybossa.feed import update_feed
from pybossa.model import update_project_timestamp
from pybossa.model.blogpost import Blogpost
from pybossa.model.project import Project
from pybossa.model.task import Task
from pybossa.model.task_run import TaskRun
from pybossa.model.user import User
from pybossa.jobs import webhook
from pybossa.core import sentinel

webhook_queue = Queue('high', connection=sentinel.master)


@event.listens_for(Blogpost, 'after_insert')
def add_blog_event(mapper, conn, target):
    """Update PyBossa feed with new blog post."""
    sql_query = ('select name, short_name, info from project \
                 where id=%s') % target.project_id
    results = conn.execute(sql_query)
    obj = dict(id=target.project_id,
               name=None,
               short_name=None,
               info=None,
               action_updated='Blog')
    for r in results:
        obj['name'] = r.name
        obj['short_name'] = r.short_name
        obj['info'] = r.info
    update_feed(obj)


@event.listens_for(Project, 'after_insert')
def add_project_event(mapper, conn, target):
    """Update PyBossa feed with new project."""
    obj = dict(id=target.id,
               name=target.name,
               short_name=target.short_name,
               action_updated='Project')
    update_feed(obj)


@event.listens_for(Task, 'after_insert')
def add_task_event(mapper, conn, target):
    """Update PyBossa feed with new task."""
    sql_query = ('select name, short_name, info from project \
                 where id=%s') % target.project_id
    results = conn.execute(sql_query)
    obj = dict(id=target.project_id,
               name=None,
               short_name=None,
               info=None,
               action_updated='Task')
    for r in results:
        obj['name'] = r.name
        obj['short_name'] = r.short_name
        obj['info'] = r.info
    update_feed(obj)


@event.listens_for(User, 'after_insert')
def add_user_event(mapper, conn, target):
    """Update PyBossa feed with new user."""
    obj = target.dictize()
    obj['action_updated']='User'
    update_feed(obj)


def add_user_contributed_to_feed(conn, user_id, project_obj):
    if user_id is not None:
        sql_query = ('select fullname, name, info from "user" \
                     where id=%s') % user_id
        results = conn.execute(sql_query)
        for r in results:
            obj = dict(id=user_id,
                       name=r.name,
                       fullname=r.fullname,
                       info=r.info,
                       project_name=project_obj['name'],
                       project_short_name=project_obj['short_name'],
                       action_updated='UserContribution')
        update_feed(obj)


def is_task_completed(conn, task_id):
    sql_query = ('select count(id) from task_run \
                 where task_run.task_id=%s') % task_id
    n_answers = conn.scalar(sql_query)
    sql_query = ('select n_answers from task \
                 where task.id=%s') % task_id
    task_n_answers = conn.scalar(sql_query)
    return (n_answers) >= task_n_answers


def update_task_state(conn, task_id):
    sql_query = ("UPDATE task SET state=\'completed\' \
                 where id=%s") % task_id
    conn.execute(sql_query)


def push_webhook(project_obj, task_id):
    if project_obj['webhook']:
        payload = dict(event="task_completed",
                       project_short_name=project_obj['short_name'],
                       project_id=project_obj['id'],
                       task_id=task_id,
                       fired_at=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"))
        webhook_queue.enqueue(webhook, project_obj['webhook'], payload)

@event.listens_for(TaskRun, 'after_insert')
def on_taskrun_submit(mapper, conn, target):
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
        project_obj['id'] = target.project_id

    add_user_contributed_to_feed(conn, target.user_id, project_obj)
    if is_task_completed(conn, target.task_id):
        update_task_state(conn, target.task_id)
        update_feed(project_obj)
        push_webhook(project_obj, target.task_id)


@event.listens_for(Blogpost, 'after_insert')
@event.listens_for(Blogpost, 'after_update')
@event.listens_for(Task, 'after_insert')
@event.listens_for(Task, 'after_update')
@event.listens_for(TaskRun, 'after_insert')
@event.listens_for(TaskRun, 'after_update')
def update_project(mapper, conn, target):
    """Update project updated timestamp."""
    update_project_timestamp(mapper, conn, target)


@event.listens_for(User, 'before_insert')
def make_admin(mapper, conn, target):
    users = conn.scalar('select count(*) from "user"')
    if users == 0:
        target.admin = True
