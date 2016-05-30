# -*- coding: utf8 -*-
# This file is part of PyBossa.
#
# Copyright (C) 2015 SciFabric LTD.
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
from pybossa.model import update_project_timestamp, update_target_timestamp
from pybossa.model import make_timestamp
from pybossa.model.blogpost import Blogpost
from pybossa.model.project import Project
from pybossa.model.task import Task
from pybossa.model.task_run import TaskRun
from pybossa.model.webhook import Webhook
from pybossa.model.user import User
from pybossa.model.result import Result
from pybossa.core import result_repo
from pybossa.jobs import webhook, notify_blog_users
from pybossa.core import sentinel

webhook_queue = Queue('high', connection=sentinel.master)
mail_queue = Queue('super', connection=sentinel.master)


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
    # Notify volunteers
    mail_queue.enqueue(notify_blog_users,
                       blog_id=target.id,
                       project_id=target.project_id)


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


def push_webhook(project_obj, task_id, result_id):
    if project_obj['webhook']:
        payload = dict(event="task_completed",
                       project_short_name=project_obj['short_name'],
                       project_id=project_obj['id'],
                       task_id=task_id,
                       result_id=result_id,
                       fired_at=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"))
        webhook_queue.enqueue(webhook, project_obj['webhook'], payload)


def create_result(conn, project_id, task_id):
    """Create a result for the given project and task."""
    sql_query = ("SELECT id FROM task_run WHERE project_id=%s \
                 AND task_id=%s") % (project_id, task_id)
    results = conn.execute(sql_query)
    task_run_ids = ", ".join(str(tr.id) for tr in results)

    sql_query = ("""SELECT id FROM result WHERE project_id=%s \
                   AND task_id=%s;""") % (project_id, task_id)

    results = conn.execute(sql_query)

    for r in results:
        if r:
            # Update result
            sql_query = ("""UPDATE result SET last_version=false \
                           WHERE id=%s;""") % (r.id)
            conn.execute(sql_query)

    sql_query = """INSERT INTO result
                   (created, project_id, task_id, task_run_ids, last_version)
                   VALUES ('%s', %s, %s, '{%s}', %s);""" % (make_timestamp(),
                                                  project_id,
                                                  task_id,
                                                  task_run_ids,
                                                  True)
    conn.execute(sql_query)

    sql_query = """SELECT id FROM result \
                WHERE project_id=%s \
                AND task_id=%s \
                AND last_version=true""" % (project_id, task_id)

    results = conn.execute(sql_query)
    for r in results:
        return r.id

@event.listens_for(TaskRun, 'after_insert')
def on_taskrun_submit(mapper, conn, target):
    """Update the task.state when n_answers condition is met."""
    # Get project details
    sql_query = ('select name, short_name, published, webhook, info from project \
                 where id=%s') % target.project_id
    results = conn.execute(sql_query)
    project_obj = dict(id=target.project_id,
                   name=None,
                   short_name=None,
                   published=False,
                   info=None,
                   webhook=None,
                   action_updated='TaskCompleted')
    for r in results:
        project_obj['name'] = r.name
        project_obj['short_name'] = r.short_name
        project_obj['published'] = r.published
        project_obj['info'] = r.info
        project_obj['webhook'] = r.webhook
        project_obj['id'] = target.project_id

    add_user_contributed_to_feed(conn, target.user_id, project_obj)
    if is_task_completed(conn, target.task_id) and project_obj['published']:
        update_task_state(conn, target.task_id)
        update_feed(project_obj)
        result_id = create_result(conn, target.project_id, target.task_id)
        push_webhook(project_obj, target.task_id, result_id)


@event.listens_for(Blogpost, 'after_insert')
@event.listens_for(Blogpost, 'after_update')
@event.listens_for(Task, 'after_insert')
@event.listens_for(Task, 'after_update')
@event.listens_for(TaskRun, 'after_insert')
@event.listens_for(TaskRun, 'after_update')
def update_project(mapper, conn, target):
    """Update project updated timestamp."""
    update_project_timestamp(mapper, conn, target)

@event.listens_for(Webhook, 'after_update')
def update_timestamp(mapper, conn, target):
    """Update domain object with timestamp."""
    update_target_timestamp(mapper, conn, target)


@event.listens_for(User, 'before_insert')
def make_admin(mapper, conn, target):
    users = conn.scalar('select count(*) from "user"')
    if users == 0:
        target.admin = True
