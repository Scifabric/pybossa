# -*- coding: utf8 -*-
# This file is part of PyBossa.
#
# Copyright (C) 2014 SF Isle of Man Limited
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
"""Jobs module for running background tasks in PyBossa server."""
from datetime import datetime
import math
from flask import current_app, render_template
from flask.ext.mail import Message
from pybossa.core import mail, task_repo, importer
from pybossa.util import with_cache_disabled


MINUTE = 60
HOUR = 60 * 60


def schedule_job(function, scheduler):
    """Schedules a job and returns a log message about success of the operation"""
    scheduled_jobs = scheduler.get_jobs()
    job = scheduler.schedule(
        scheduled_time=(function.get('scheduled_time') or datetime.utcnow()),
        func=function['name'],
        args=function['args'],
        kwargs=function['kwargs'],
        interval=function['interval'],
        repeat=None,
        timeout=function['timeout'])
    for sj in scheduled_jobs:
        if (function['name'].__name__ in sj.func_name and
                sj.args == function['args'] and
                sj.kwargs == function['kwargs']):
            job.cancel()
            msg = ('WARNING: Job %s(%s, %s) is already scheduled'
                   % (function['name'].__name__, function['args'],
                      function['kwargs']))
            return msg
    msg = ('Scheduled %s(%s, %s) to run every %s seconds'
           % (function['name'].__name__, function['args'], function['kwargs'],
              function['interval']))
    return msg


def get_quarterly_date(now):
    if not isinstance(now, datetime):
        raise TypeError('Expected %s, got %s' % (type(datetime), type(now)))
    execute_month = int(math.ceil(now.month / 3.0) * 3)
    execute_day = 31 if execute_month in [3, 12] else 30
    execute_date = datetime(now.year, execute_month, execute_day)
    return datetime.combine(execute_date, now.time())


def schedule_priority_jobs(queue_name, interval):
    """Schedule all PyBossa high priority jobs."""
    from pybossa.core import sentinel
    from rq import Queue
    redis_conn = sentinel.master

    jobs_generator = get_scheduled_jobs()
    n_jobs = 0
    queue = Queue(queue_name, connection=redis_conn)
    for job_gen in jobs_generator:
        for job in job_gen:
            if (job['queue'] == queue_name):
                n_jobs += 1
                queue.enqueue_call(func=job['name'],
                                   args=job['args'],
                                   kwargs=job['kwargs'],
                                   timeout=job['timeout'])
    msg = "%s jobs in %s have been enqueued" % (n_jobs, queue_name)
    return msg

def get_default_jobs(): # pragma: no cover
    """Return default jobs."""
    yield dict(name=warm_up_stats, args=[], kwargs={},
               timeout=(10 * MINUTE), queue='high')
    yield dict(name=warn_old_project_owners, args=[], kwargs={},
               timeout=(10 * MINUTE), queue='low')
    yield dict(name=warm_cache, args=[], kwargs={},
               timeout=(10 * MINUTE), queue='super')


def get_scheduled_jobs(): # pragma: no cover
    """Return a list of scheduled jobs."""
    # Default ones
    # A job is a dict with the following format: dict(name, args, kwargs,
    # timeout, queue)
    jobs = get_default_jobs()
    # Create ZIPs for all projects
    zip_jobs = get_export_task_jobs()
    # Based on type of user
    project_jobs = get_project_jobs()
    autoimport_jobs = get_autoimport_jobs()
    # User engagement jobs
    engage_jobs = get_inactive_users_jobs()
    non_contrib_jobs = get_non_contributors_users_jobs()
    return [zip_jobs, jobs, project_jobs, autoimport_jobs, \
           engage_jobs, non_contrib_jobs]


def get_export_task_jobs():
    """Export tasks to zip"""
    from pybossa.core import db, user_repo
    from pybossa.model.project import App
    apps = db.slave_session.query(App).all()
    for app_x in apps:
        checkuser = user_repo.get(app_x.owner_id)
        # Check if Pro User, if yes use a higher priority queue
        queue = 'low'
        if checkuser.pro:
            queue = 'high'
        job = dict(name=project_export,
                   args=[app_x.id], kwargs={},
                   timeout=(10 * MINUTE),
                   queue=queue)
        yield job


def project_export(id):
    from pybossa.core import project_repo, json_exporter, csv_exporter
    app = project_repo.get(id)
    if app is not None:
        print "Export project id %d" % id
        json_exporter.pregenerate_zip_files(app)
        csv_exporter.pregenerate_zip_files(app)


def get_project_jobs():
    """Return a list of jobs based on user type."""
    from pybossa.cache import projects as cached_projects
    return create_dict_jobs(cached_projects.get_from_pro_user(),
                            get_project_stats,
                            timeout=(10 * MINUTE),
                            queue='super')


def create_dict_jobs(data, function, timeout=(10 * MINUTE), queue='low'):
    for d in data:
        jobs =  dict(name=function,
                     args=[d['id'], d['short_name']], kwargs={},
                     timeout=timeout,
                     queue=queue)
        yield jobs


def get_autoimport_jobs(queue='low'):
    from pybossa.core import project_repo
    import pybossa.cache.projects as cached_projects
    pro_user_projects = cached_projects.get_from_pro_user()
    for project_dict in pro_user_projects:
        project = project_repo.get(project_dict['id'])
        if project.has_autoimporter():
            job = dict(name=import_tasks,
                       args=[project.id],
                       kwargs=project.get_autoimporter(),
                       timeout=(10 * MINUTE),
                       queue=queue)
            yield job


@with_cache_disabled
def get_project_stats(id, short_name): # pragma: no cover
    """Get stats for app."""
    import pybossa.cache.apps as cached_apps
    import pybossa.cache.project_stats as stats
    from flask import current_app

    cached_apps.get_app(short_name)
    cached_apps.n_tasks(id)
    cached_apps.n_task_runs(id)
    cached_apps.overall_progress(id)
    cached_apps.last_activity(id)
    cached_apps.n_completed_tasks(id)
    cached_apps.n_volunteers(id)
    stats.get_stats(id, current_app.config.get('GEO'))


@with_cache_disabled
def warm_up_stats(): # pragma: no cover
    """Background job for warming stats."""
    print "Running on the background warm_up_stats"
    from pybossa.cache.site_stats import (n_auth_users, n_anon_users,
                                          n_tasks_site, n_total_tasks_site,
                                          n_task_runs_site,
                                          get_top5_projects_24_hours,
                                          get_top5_users_24_hours, get_locs)
    n_auth_users()
    n_anon_users()
    n_tasks_site()
    n_total_tasks_site()
    n_task_runs_site()
    get_top5_projects_24_hours()
    get_top5_users_24_hours()
    get_locs()

    return True


@with_cache_disabled
def warm_cache():  # pragma: no cover
    """Background job to warm cache."""
    from pybossa.core import create_app
    app = create_app(run_as_server=False)
    # Cache 3 pages
    apps_cached = []
    pages = range(1, 4)
    import pybossa.cache.apps as cached_apps
    import pybossa.cache.categories as cached_cat
    import pybossa.cache.users as cached_users
    import pybossa.cache.project_stats as stats

    def warm_app(id, short_name, featured=False):
        if id not in apps_cached:
            cached_apps.get_app(short_name)
            cached_apps.n_tasks(id)
            n_task_runs = cached_apps.n_task_runs(id)
            cached_apps.overall_progress(id)
            cached_apps.last_activity(id)
            cached_apps.n_completed_tasks(id)
            cached_apps.n_volunteers(id)
            if n_task_runs >= 1000 or featured:
                print ("Getting stats for %s as it has %s task runs" %
                       (short_name, n_task_runs))
                stats.get_stats(id, app.config.get('GEO'))
            apps_cached.append(id)

    # Cache top projects
    apps = cached_apps.get_top()
    for a in apps:
        warm_app(a['id'], a['short_name'])
    for page in pages:
        apps = cached_apps.get_featured('featured', page,
                                        app.config['APPS_PER_PAGE'])
        for a in apps:
            warm_app(a['id'], a['short_name'], featured=True)

    # Categories
    categories = cached_cat.get_used()
    for c in categories:
        for page in pages:
            apps = cached_apps.get(c['short_name'],
                                   page,
                                   app.config['APPS_PER_PAGE'])
            for a in apps:
                warm_app(a['id'], a['short_name'])
    # Users
    users = cached_users.get_leaderboard(app.config['LEADERBOARD'], 'anonymous')
    for user in users:
        print "Getting stats for %s" % user['name']
        cached_users.get_user_summary(user['name'])
        cached_users.projects_contributed_cached(user['id'])
        cached_users.published_projects_cached(user['id'])
        cached_users.draft_projects_cached(user['id'])

    cached_users.get_top()

    return True


def get_non_updated_apps():
    """Return a list of non updated apps."""
    from sqlalchemy.sql import text
    from pybossa.model.project import App
    from pybossa.core import db
    sql = text('''SELECT id FROM app WHERE TO_DATE(updated,
                'YYYY-MM-DD\THH24:MI:SS.US') <= NOW() - '3 month':: INTERVAL
               AND contacted != True LIMIT 25''')
    results = db.slave_session.execute(sql)
    apps = []
    for row in results:
        a = App.query.get(row.id)
        apps.append(a)
    return apps


def warn_old_project_owners():
    """E-mail the project owners not updated in the last 3 months."""
    from pybossa.core import mail, project_repo
    from flask import current_app
    from flask.ext.mail import Message

    apps = get_non_updated_apps()

    with mail.connect() as conn:
        for a in apps:
            message = ("Dear %s,\
                       \
                       Your project %s has been inactive for the last 3 months.\
                       And we would like to inform you that if you need help \
                       with it, just contact us answering to this email.\
                       \
                       Otherwise, we will archive the project, removing it \
                       from the server. You have one month to upload any new \
                       tasks, add a new blog post, or engage new volunteers.\
                       \
                       If at the end the project is deleted, we will send you \
                       a ZIP file where you can download your project.\
                       \
                       All the best,\
                       \
                       The team.") % (a.owner.fullname, a.name)
            subject = ('Your %s project: %s has been inactive'
                       % (current_app.config.get('BRAND'), a.name))
            msg = Message(recipients=[a.owner.email_addr],
                          body=message,
                          subject=subject)
            conn.send(msg)
            a.contacted = True
            project_repo.update(a)
    return True


def send_mail(message_dict):
    message = Message(**message_dict)
    mail.send(message)


def import_tasks(project_id, **form_data):
    from pybossa.core import project_repo
    app = project_repo.get(project_id)
    msg = importer.create_tasks(task_repo, project_id, **form_data)
    msg = msg + ' to your project %s!' % app.name
    subject = 'Tasks Import to your project %s' % app.name
    body = 'Hello,\n\n' + msg + '\n\nAll the best,\nThe %s team.'\
        % current_app.config.get('BRAND')
    mail_dict = dict(recipients=[app.owner.email_addr],
                     subject=subject, body=body)
    send_mail(mail_dict)
    return msg


def get_inactive_users_jobs(queue='quaterly'):
    """Return a list of inactive users that have contributed to a project."""
    from sqlalchemy.sql import text
    from pybossa.model.user import User
    from pybossa.core import db
    from pybossa.extensions import misaka
    # First users that have participated once but more than 3 months ago
    sql = text('''SELECT user_id FROM task_run
               WHERE user_id IS NOT NULL
               AND TO_DATE(task_run.finish_time, 'YYYY-MM-DD\THH24:MI:SS.US')
               <= NOW() - '3 month'::INTERVAL GROUP BY task_run.user_id;''')
    results = db.slave_session.execute(sql)
    for row in results:

        user = User.query.get(row.user_id)

        if user.subscribed:
            subject = "We miss you!"
            body = render_template('/account/email/inactive.md',
                                   user=user.dictize(),
                                   config=current_app.config)
            html = render_template('/account/email/inactive.html',
                                   user=user.dictize(),
                                   config=current_app.config)

            mail_dict = dict(recipients=[user.email_addr],
                             subject=subject,
                             body=body,
                             html=html)

            job = dict(name=send_mail,
                       args=[mail_dict],
                       kwargs={},
                       timeout=(10 * MINUTE),
                       queue=queue)
            yield job

def get_non_contributors_users_jobs(queue='quaterly'):
    """Return a list of users that have never contributed to a project."""
    from sqlalchemy.sql import text
    from pybossa.model.user import User
    from pybossa.core import db
    from pybossa.extensions import misaka
    # Second users that have created an account but never participated
    sql = text('''SELECT id FROM "user" WHERE
               NOT EXISTS (SELECT user_id FROM task_run
               WHERE task_run.user_id="user".id)''')
    results = db.slave_session.execute(sql)
    for row in results:
        user = User.query.get(row.id)

        if user.subscribed:
            subject = "Why don't you help us?!"
            body = render_template('/account/email/noncontributors.md',
                                   user=user.dictize(),
                                   config=current_app.config)
            html = render_template('/account/email/noncontributors.html',
                                   user=user.dictize(),
                                   config=current_app.config)
            mail_dict = dict(recipients=[user.email_addr],
                             subject=subject,
                             body=body,
                             html=html)

            job = dict(name=send_mail,
                       args=[mail_dict],
                       kwargs={},
                       timeout=(10 * MINUTE),
                       queue=queue)
            yield job
