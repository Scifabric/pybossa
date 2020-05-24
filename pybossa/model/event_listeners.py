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
from datetime import datetime
from flask import current_app

from rq import Queue
from sqlalchemy import event

from flask import url_for

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
from pybossa.model.counter import Counter
from pybossa.core import result_repo, db
from pybossa.jobs import webhook, notify_blog_users
from pybossa.jobs import push_notification
from pybossa import sched

from pybossa.core import sentinel

webhook_queue = Queue('high', connection=sentinel.master)
mail_queue = Queue('email', connection=sentinel.master)
webpush_queue = Queue('webpush', connection=sentinel.master)


@event.listens_for(Blogpost, 'after_insert')
def add_blog_event(mapper, conn, target):
    """Update PYBOSSA feed with new blog post."""
    sql_query = ('select name, short_name, info from project \
                 where id=%s') % target.project_id
    results = conn.execute(sql_query)
    obj = dict(action_updated='Blog')
    tmp = dict()
    for r in results:
        tmp['id'] = target.project_id
        tmp['name'] = r.name
        tmp['short_name'] = r.short_name
        tmp['info'] = r.info
    tmp = Project().to_public_json(tmp)
    obj.update(tmp)
    update_feed(obj)
    # Notify volunteers
    if current_app.config.get('DISABLE_EMAIL_NOTIFICATIONS') is None:
        scheme = current_app.config.get('PREFERRED_URL_SCHEME', 'http')
        mail_queue.enqueue(notify_blog_users,
                           blog_id=target.id,
                           project_id=target.project_id)
        contents = {"en": "New update!"}
        headings = {"en": target.title}
        launch_url = url_for('project.show_blogpost',
                             short_name=tmp['short_name'],
                             id=target.id,
                             _scheme=scheme,
                             _external=True)
        print(launch_url)
        web_buttons = [{"id": "read-more-button",
                        "text": "Read more",
                        "icon": "http://i.imgur.com/MIxJp1L.png",
                        "url": launch_url }]
        webpush_queue.enqueue(push_notification,
                              project_id=target.project_id,
                              contents=contents,
                              headings=headings,
                              web_buttons=web_buttons,
                              launch_url=launch_url)


@event.listens_for(Project, 'after_insert')
def add_project_event(mapper, conn, target):
    """Update PYBOSSA feed with new project."""
    tmp = dict(id=target.id,
               name=target.name,
               short_name=target.short_name,
               info=target.info)
    obj = dict(action_updated='Project')
    tmp = Project().to_public_json(tmp)
    obj.update(tmp)
    update_feed(obj)
    # Create a clean projectstats object for it
    sql_query = """INSERT INTO project_stats
                   (project_id, n_tasks, n_task_runs, n_results, n_volunteers,
                   n_completed_tasks, overall_progress, average_time,
                   n_blogposts, last_activity, info)
                   VALUES (%s, 0, 0, 0, 0, 0, 0, 0, 0, 0, '{}');""" % (target.id)
    conn.execute(sql_query)


@event.listens_for(Task, 'after_insert')
def add_task_event(mapper, conn, target):
    """Update PYBOSSA feed with new task."""
    sql_query = ('select name, short_name, info from project \
                 where id=%s') % target.project_id
    results = conn.execute(sql_query)
    obj = dict(action_updated='Task')
    tmp = dict()
    for r in results:
        tmp['id'] = target.project_id
        tmp['name'] = r.name
        tmp['short_name'] = r.short_name
        tmp['info'] = r.info
    tmp = Project().to_public_json(tmp)
    obj.update(tmp)
    update_feed(obj)


@event.listens_for(User, 'after_insert')
def add_user_event(mapper, conn, target):
    """Update PYBOSSA feed with new user."""
    obj = target.to_public_json()
    obj['action_updated'] = 'User'
    update_feed(obj)


def add_user_contributed_to_feed(conn, user_id, project_obj):
    if user_id is not None:
        sql_query = ('select fullname, name, info from "user" \
                     where id=%s and restrict=false') % user_id
        results = conn.execute(sql_query)
        tmp = None
        for r in results:
            tmp = dict(id=user_id,
                       name=r.name,
                       fullname=r.fullname,
                       info=r.info)
            tmp = User().to_public_json(tmp)
            tmp['project_id'] = project_obj['id']
            tmp['project_name'] = project_obj['name']
            tmp['project_short_name'] = project_obj['short_name']
            tmp['category_id'] = project_obj['category_id']
            tmp['action_updated'] = 'UserContribution'
        if tmp:
            update_feed(tmp)


def is_task_completed(conn, task_id, project_id):
    sql_query = ('select count(id) from task_run \
                 where task_run.task_id=%s and \
                 task_run.project_id=%s') % (task_id, project_id)
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
    sql_query = ('select name, short_name, published, webhook, info, category_id \
                 from project where id=%s') % target.project_id
    results = conn.execute(sql_query)
    tmp = dict()
    for r in results:
        tmp['name'] = r.name
        tmp['short_name'] = r.short_name
        _published = r.published
        tmp['info'] = r.info
        _webhook = r.webhook
        tmp['category_id'] = r.category_id
        tmp['id'] = target.project_id

    project_public = dict()
    project_public.update(Project().to_public_json(tmp))
    project_public['action_updated'] = 'TaskCompleted'

    sched.after_save(target, conn)
    add_user_contributed_to_feed(conn, target.user_id, project_public)
    if is_task_completed(conn, target.task_id, target.project_id):
        update_task_state(conn, target.task_id)
        update_feed(project_public)
        result_id = create_result(conn, target.project_id, target.task_id)
        project_private = dict()
        project_private.update(project_public)
        project_private['webhook'] = _webhook
        push_webhook(project_private, target.task_id, result_id)

    # Every time a registered user contributes a taskrun its notified_at column is reset
    # so the job for deleting inactive accounts, is not triggered
    if target.user_id:
        sql = f"update \"user\" set notified_at=null where \"user\".id={target.user_id};"
        conn.execute(sql)


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

@event.listens_for(Blogpost, 'after_update')
def update_timestamp(mapper, conn, target):
    """Update domain object with timestamp."""
    update_target_timestamp(mapper, conn, target)


@event.listens_for(User, 'before_insert')
def make_admin(mapper, conn, target):
    users = conn.scalar('select count(*) from "user" where restrict=false')
    if users == 0:
        target.admin = True


@event.listens_for(Task, 'after_insert')
def create_zero_counter(mapper, conn, target):
    sql_query = ("insert into counter(created, project_id, task_id, n_task_runs) \
                 VALUES (TIMESTAMP '%s', %s, %s, 0)"
                 % (make_timestamp(), target.project_id, target.id))
    conn.execute(sql_query)


@event.listens_for(Task, 'after_delete')
def delete_task_counter(mapper, conn, target):
    sql_query = ("delete from counter where project_id=%s and task_id=%s"
                 % (target.project_id, target.id))
    conn.execute(sql_query)


@event.listens_for(TaskRun, 'after_insert')
def increase_task_counter(mapper, conn, target):
    sql_query = ("insert into counter(created, project_id, task_id, n_task_runs) \
                 VALUES (TIMESTAMP '%s', %s, %s, 1)"
                 % (make_timestamp(), target.project_id, target.task_id))
    conn.execute(sql_query)


@event.listens_for(TaskRun, 'after_delete')
def decrease_task_counter(mapper, conn, target):
    sql_query = ("insert into counter(created, project_id, task_id, n_task_runs) \
                 VALUES (TIMESTAMP '%s', %s, %s, -1)"
                 % (make_timestamp(), target.project_id, target.task_id))
    conn.execute(sql_query)
