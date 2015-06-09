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
"""Jobs module for running background tasks in PyBossa server."""
from datetime import datetime
import math
from flask import current_app, render_template
from flask.ext.mail import Message
from pybossa.core import mail, task_repo, importer
from pybossa.util import with_cache_disabled
import pybossa.dashboard.jobs as dashboard


MINUTE = 60
HOUR = 60 * 60


def schedule_job(function, scheduler):
    """Schedule a job and return a log message."""
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
    """Get quarterly date."""
    if not isinstance(now, datetime):
        raise TypeError('Expected %s, got %s' % (type(datetime), type(now)))
    execute_month = int(math.ceil(now.month / 3.0) * 3)
    execute_day = 31 if execute_month in [3, 12] else 30
    execute_date = datetime(now.year, execute_month, execute_day)
    return datetime.combine(execute_date, now.time())


def enqueue_periodic_jobs(queue_name):
    """Enqueue all PyBossa periodic jobs."""
    from pybossa.core import sentinel
    from rq import Queue
    redis_conn = sentinel.master

    jobs_generator = get_periodic_jobs(queue_name)
    n_jobs = 0
    queue = Queue(queue_name, connection=redis_conn)
    for job in jobs_generator:
        if (job['queue'] == queue_name):
            n_jobs += 1
            queue.enqueue_call(func=job['name'],
                               args=job['args'],
                               kwargs=job['kwargs'],
                               timeout=job['timeout'])
    msg = "%s jobs in %s have been enqueued" % (n_jobs, queue_name)
    return msg


def get_periodic_jobs(queue):
    """Return a list of periodic jobs for a given queue."""
    # A job is a dict with the following format: dict(name, args, kwargs,
    # timeout, queue)
    # Default ones
    jobs = get_default_jobs()
    # Create ZIPs for all projects
    zip_jobs = get_export_task_jobs(queue) if queue in ('high', 'low') else []
    # Based on type of user
    project_jobs = get_project_jobs() if queue == 'super' else []
    autoimport_jobs = get_autoimport_jobs() if queue == 'low' else []
    # User engagement jobs
    engage_jobs = get_inactive_users_jobs() if queue == 'quaterly' else []
    non_contrib_jobs = get_non_contributors_users_jobs() \
        if queue == 'quaterly' else []
    dashboard_jobs = get_dashboard_jobs() if queue == 'low' else []
    _all = [zip_jobs, jobs, project_jobs, autoimport_jobs,
            engage_jobs, non_contrib_jobs, dashboard_jobs]
    return (job for sublist in _all for job in sublist if job['queue'] == queue)


def get_default_jobs():  # pragma: no cover
    """Return default jobs."""
    yield dict(name=warm_up_stats, args=[], kwargs={},
               timeout=(10 * MINUTE), queue='high')
    yield dict(name=warn_old_project_owners, args=[], kwargs={},
               timeout=(10 * MINUTE), queue='low')
    yield dict(name=warm_cache, args=[], kwargs={},
               timeout=(10 * MINUTE), queue='super')


def get_export_task_jobs(queue):
    """Export tasks to zip."""
    from pybossa.core import project_repo
    import pybossa.cache.projects as cached_projects
    if queue == 'high':
        projects = cached_projects.get_from_pro_user()
    else:
        projects = (p.dictize() for p in project_repo.get_all()
                    if p.owner.pro is False)
    for project in projects:
        project_id = project.get('id')
        job = dict(name=project_export,
                   args=[project_id], kwargs={},
                   timeout=(10 * MINUTE),
                   queue=queue)
        yield job


def project_export(_id):
    """Export project."""
    from pybossa.core import project_repo, json_exporter, csv_exporter
    app = project_repo.get(_id)
    if app is not None:
        print "Export project id %d" % _id
        json_exporter.pregenerate_zip_files(app)
        csv_exporter.pregenerate_zip_files(app)


def get_project_jobs(queue='super'):
    """Return a list of jobs based on user type."""
    from pybossa.cache import projects as cached_projects
    return create_dict_jobs(cached_projects.get_from_pro_user(),
                            get_project_stats,
                            timeout=(10 * MINUTE),
                            queue=queue)


def create_dict_jobs(data, function, timeout=(10 * MINUTE), queue='low'):
    """Create a dict job."""
    for d in data:
        jobs = dict(name=function,
                    args=[d['id'], d['short_name']], kwargs={},
                    timeout=timeout,
                    queue=queue)
        yield jobs


def get_inactive_users_jobs(queue='quaterly'):
    """Return a list of inactive users that have contributed to a project."""
    from sqlalchemy.sql import text
    from pybossa.model.user import User
    from pybossa.core import db
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


def get_dashboard_jobs(queue='low'):  # pragma: no cover
    """Return dashboard jobs."""
    yield dict(name=dashboard.active_users_week, args=[], kwargs={},
               timeout=(10 * MINUTE), queue=queue)
    yield dict(name=dashboard.active_anon_week, args=[], kwargs={},
               timeout=(10 * MINUTE), queue=queue)
    yield dict(name=dashboard.new_projects_week, args=[], kwargs={},
               timeout=(10 * MINUTE), queue=queue)
    yield dict(name=dashboard.update_projects_week, args=[], kwargs={},
               timeout=(10 * MINUTE), queue=queue)
    yield dict(name=dashboard.new_tasks_week, args=[], kwargs={},
               timeout=(10 * MINUTE), queue=queue)
    yield dict(name=dashboard.new_task_runs_week, args=[], kwargs={},
               timeout=(10 * MINUTE), queue=queue)
    yield dict(name=dashboard.new_users_week, args=[], kwargs={},
               timeout=(10 * MINUTE), queue=queue)
    yield dict(name=dashboard.returning_users_week, args=[], kwargs={},
               timeout=(10 * MINUTE), queue=queue)


def get_non_contributors_users_jobs(queue='quaterly'):
    """Return a list of users that have never contributed to a project."""
    from sqlalchemy.sql import text
    from pybossa.model.user import User
    from pybossa.core import db
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


def get_autoimport_jobs(queue='low'):
    """Get autoimport jobs."""
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


# The following are the actual jobs (i.e. tasks performed in the background)

@with_cache_disabled
def get_project_stats(_id, short_name):  # pragma: no cover
    """Get stats for project."""
    import pybossa.cache.projects as cached_projects
    import pybossa.cache.project_stats as stats
    from flask import current_app

    cached_projects.get_project(short_name)
    cached_projects.n_tasks(_id)
    cached_projects.n_task_runs(_id)
    cached_projects.overall_progress(_id)
    cached_projects.last_activity(_id)
    cached_projects.n_completed_tasks(_id)
    cached_projects.n_volunteers(_id)
    stats.get_stats(_id, current_app.config.get('GEO'))


@with_cache_disabled
def warm_up_stats():  # pragma: no cover
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
    projects_cached = []
    import pybossa.cache.projects as cached_projects
    import pybossa.cache.categories as cached_cat
    import pybossa.cache.users as cached_users
    import pybossa.cache.project_stats as stats
    from pybossa.util import rank

    def warm_project(_id, short_name, featured=False):
        if _id not in projects_cached:
            cached_projects.get_project(short_name)
            cached_projects.n_tasks(_id)
            n_task_runs = cached_projects.n_task_runs(_id)
            cached_projects.overall_progress(_id)
            cached_projects.last_activity(_id)
            cached_projects.n_completed_tasks(_id)
            cached_projects.n_volunteers(_id)
            if n_task_runs >= 1000 or featured:
                # print ("Getting stats for %s as it has %s task runs" %
                #        (short_name, n_task_runs))
                stats.get_stats(_id, app.config.get('GEO'))
            projects_cached.append(_id)

    # Cache top projects
    projects = cached_projects.get_top()
    for p in projects:
        warm_project(p['id'], p['short_name'])

    # Cache 3 pages
    to_cache = 3 * app.config['APPS_PER_PAGE']
    projects = rank(cached_projects.get_all_featured('featured'))[:to_cache]
    for p in projects:
        warm_project(p['id'], p['short_name'], featured=True)

    # Categories
    categories = cached_cat.get_used()
    for c in categories:
        projects = rank(cached_projects.get_all(c['short_name']))[:to_cache]
        for p in projects:
            warm_project(p['id'], p['short_name'])
    # Users
    users = cached_users.get_leaderboard(app.config['LEADERBOARD'], 'anonymous')
    for user in users:
        # print "Getting stats for %s" % user['name']
        cached_users.get_user_summary(user['name'])
        cached_users.projects_contributed_cached(user['id'])
        cached_users.published_projects_cached(user['id'])
        cached_users.draft_projects_cached(user['id'])

    cached_users.get_top()

    return True


def get_non_updated_projects():
    """Return a list of non updated projects."""
    from sqlalchemy.sql import text
    from pybossa.model.project import Project
    from pybossa.core import db
    sql = text('''SELECT id FROM project WHERE TO_DATE(updated,
                'YYYY-MM-DD\THH24:MI:SS.US') <= NOW() - '3 month':: INTERVAL
               AND contacted != True LIMIT 25''')
    results = db.slave_session.execute(sql)
    projects = []
    for row in results:
        a = Project.query.get(row.id)
        projects.append(a)
    return projects


def warn_old_project_owners():
    """E-mail the project owners not updated in the last 3 months."""
    from pybossa.core import mail, project_repo
    from flask.ext.mail import Message

    projects = get_non_updated_projects()

    with mail.connect() as conn:
        for project in projects:
            subject = ('Your %s project: %s has been inactive'
                       % (current_app.config.get('BRAND'), project.name))
            body = render_template('/account/email/inactive_project.md',
                                   project=project)
            html = render_template('/account/email/inactive_project.html',
                                   project=project)
            msg = Message(recipients=[project.owner.email_addr],
                          subject=subject,
                          body=body,
                          html=html)
            conn.send(msg)
            project.contacted = True
            project_repo.update(project)
    return True


def send_mail(message_dict):
    """Send email."""
    message = Message(**message_dict)
    mail.send(message)


def import_tasks(project_id, **form_data):
    """Import tasks for a project."""
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
