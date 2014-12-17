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
from flask.ext.mail import Message
from pybossa.core import mail
from pybossa.util import with_cache_disabled


MINUTE = 60
HOUR = 60 * 60

def schedule_priority_jobs(queue_name, interval):
    """Schedule all PyBossa high priority jobs."""
    jobs = get_scheduled_jobs()
    from pybossa.core import sentinel
    from rq import Queue
    redis_conn = sentinel.master

    n_jobs = 0
    queue = Queue(queue_name, connection=redis_conn)
    for job in jobs:
        if (job['queue'] == queue_name):
            n_jobs += 1
            queue.enqueue_call(func=job['name'],
                               args=job['args'],
                               kwargs=job['kwargs'],
                               timeout=job['timeout'])
    msg = "%s jobs in %s have been enqueued" % (n_jobs, queue_name)
    return msg


def get_scheduled_jobs(): # pragma: no cover
    """Return a list of scheduled jobs."""
    # Default ones
    # A job is a dict with the following format: dict(name, args, kwargs,
    # interval)
    jobs = [
            dict(name=warm_up_stats, args=[], kwargs={},
                 interval=HOUR, timeout=(10 * MINUTE), queue='high'),
            dict(name=warn_old_project_owners, args=[], kwargs={},
                 interval=(24 * HOUR), timeout=(10 * MINUTE), queue='low'),
            dict(name=warm_cache, args=[], kwargs={},
                 interval=(10 * MINUTE), timeout=(10 * MINUTE), queue='super')]
    # Create ZIPs for all projects
    zip_jobs = get_export_task_jobs()
    # Based on type of user
    project_jobs = get_project_jobs()
    return zip_jobs + jobs + project_jobs

def get_export_task_jobs():
    """Export tasks to zip"""
    from pybossa.core import db, user_repo
    from pybossa.model.app import App
    apps = db.slave_session.query(App).all()
    # Append all ZIP generation for each app as a task
    jobs = []
    for app_x in apps:
        checkuser = user_repo.get(app_x.owner_id)
        # Check if Pro User, if yes use a shorter schedule
        schedule_hours = 24
        queue = 'low'
        if checkuser.pro:
            schedule_hours = 4
            queue = 'high'
        jobs.append(dict(name = project_export,
                         args = [app_x.id], kwargs={},
                         interval=(schedule_hours * HOUR),
                         timeout = (10 * MINUTE),
                         queue=queue))
    return jobs

def project_export(id):
    from pybossa.core import project_repo, json_exporter, csv_exporter
    app = project_repo.get(id)
    if app is not None:
        print "Export project id %d" % id
        json_exporter.pregenerate_zip_files(app)
        csv_exporter.pregenerate_zip_files(app)

def get_project_jobs():
    """Return a list of jobs based on user type."""
    from pybossa.cache import apps as cached_apps
    return create_dict_jobs(cached_apps.get_from_pro_user(),
                            get_app_stats,
                            interval=(10 * MINUTE),
                            timeout=(10 * MINUTE),
                            queue='super')

def create_dict_jobs(data, function,
                     interval=(24 * HOUR), timeout=(10 * MINUTE),
                     queue='low'):
    jobs = []
    for d in data:
        jobs.append(dict(name=function,
                         args=[d['id'], d['short_name']], kwargs={},
                         interval=interval,
                         timeout=timeout,
                         queue=queue))
    return jobs


@with_cache_disabled
def get_app_stats(id, short_name): # pragma: no cover
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
                                          get_top5_apps_24_hours,
                                          get_top5_users_24_hours, get_locs)
    n_auth_users()
    n_anon_users()
    n_tasks_site()
    n_total_tasks_site()
    n_task_runs_site()
    get_top5_apps_24_hours()
    get_top5_users_24_hours()
    get_locs()

    return True


@with_cache_disabled
def warm_cache(): # pragma: no cover
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
        cached_users.apps_contributed_cached(user['id'])
        cached_users.published_apps_cached(user['id'])
        cached_users.draft_apps_cached(user['id'])

    cached_users.get_top()

    return True


def get_non_updated_apps():
    """Return a list of non updated apps."""
    from sqlalchemy.sql import text
    from pybossa.model.app import App
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


def import_tasks(tasks_info, app_id):
    from pybossa.core import task_repo, project_repo
    from flask import current_app
    import pybossa.importers as importers

    app = project_repo.get(app_id)
    msg = importers.create_tasks(task_repo, tasks_info, app_id)
    msg = msg + ' to your project %s!' % app.name
    subject = 'Tasks Import to your project %s' % app.name
    body = 'Hello,\n\n' + msg + '\n\nAll the best,\nThe %s team.' % current_app.config.get('BRAND')
    mail_dict = dict(recipients=[app.owner.email_addr],
                     subject=subject, body=body)
    send_mail(mail_dict)
    return msg
