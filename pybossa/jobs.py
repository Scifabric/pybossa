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
"""Jobs module for running background tasks in PYBOSSA server."""
from datetime import datetime
import math
import requests
from flask import current_app, render_template
from flask_mail import Message, Attachment
from pybossa.core import mail, task_repo, importer, create_app
from pybossa.model.webhook import Webhook
from pybossa.util import with_cache_disabled, publish_channel, mail_with_enabled_users, UnicodeWriter
import pybossa.dashboard.jobs as dashboard
from pybossa.leaderboard.jobs import leaderboard
from pbsonesignal import PybossaOneSignal
import os
from datetime import datetime
from pybossa.core import user_repo
from rq.timeouts import JobTimeoutException
import app_settings
from pybossa.cache import sentinel, management_dashboard_stats
from pybossa.cache import settings, site_stats
from pybossa.cache.users import get_users_for_report
from pybossa.cloud_store_api.connection import create_connection
from collections import OrderedDict
import json
from StringIO import StringIO
from zipfile import ZipFile

MINUTE = 60
IMPORT_TASKS_TIMEOUT = (20 * MINUTE)
TASK_DELETE_TIMEOUT = (60 * MINUTE)
EXPORT_TASKS_TIMEOUT = (10 * MINUTE)
from pybossa.core import uploader
from pybossa.exporter.json_export import JsonExporter


def schedule_job(function, scheduler):
    """Schedule a job and return a log message."""
    scheduled_jobs = scheduler.get_jobs()
    for sj in scheduled_jobs:
        if (function['name'].__name__ in sj.description and
            sj.args == function['args'] and
                sj.kwargs == function['kwargs']):
            sj.cancel()
            msg = ('WARNING: Job %s(%s, %s) is already scheduled'
                   % (function['name'].__name__, function['args'],
                      function['kwargs']))
            return msg
    # If job was scheduled, it exists up here, else it continues
    job = scheduler.schedule(
        scheduled_time=(function.get('scheduled_time') or datetime.utcnow()),
        func=function['name'],
        args=function['args'],
        kwargs=function['kwargs'],
        interval=function['interval'],
        repeat=None,
        timeout=function['timeout'])

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


def enqueue_job(job):
    """Enqueues a job."""
    from pybossa.core import sentinel
    from rq import Queue
    redis_conn = sentinel.master
    queue = Queue(job['queue'], connection=redis_conn)
    queue.enqueue_call(func=job['name'],
                       args=job['args'],
                       kwargs=job['kwargs'],
                       timeout=job['timeout'])
    return True

def enqueue_periodic_jobs(queue_name):
    """Enqueue all PYBOSSA periodic jobs."""
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
    # Based on type of user
    project_jobs = get_project_jobs(queue) if queue in ('super', 'high') else []
    autoimport_jobs = get_autoimport_jobs() if queue == 'low' else []
    # User engagement jobs
    engage_jobs = get_inactive_users_jobs() if queue == 'quaterly' else []
    non_contrib_jobs = get_non_contributors_users_jobs() \
        if queue == 'quaterly' else []
    dashboard_jobs = get_dashboard_jobs() if queue == 'low' else []
    leaderboard_jobs = get_leaderboard_jobs() if queue == 'super' else []
    weekly_update_jobs = get_weekly_stats_update_projects() if queue == 'low' else []
    failed_jobs = get_maintenance_jobs() if queue == 'maintenance' else []
    _all = [jobs, project_jobs, autoimport_jobs,
            engage_jobs, non_contrib_jobs, dashboard_jobs,
            weekly_update_jobs, failed_jobs, leaderboard_jobs]
    return (job for sublist in _all for job in sublist if job['queue'] == queue)


def get_default_jobs():  # pragma: no cover
    """Return default jobs."""
    timeout = current_app.config.get('TIMEOUT')
    unpublish_projects = current_app.config.get('UNPUBLISH_PROJECTS')
    yield dict(name=warm_up_stats, args=[], kwargs={},
               timeout=timeout, queue='high')
    if unpublish_projects:
        yield dict(name=warn_old_project_owners, args=[], kwargs={},
                   timeout=timeout, queue='low')
    yield dict(name=warm_cache, args=[], kwargs={},
               timeout=timeout, queue='super')
    yield dict(name=news, args=[], kwargs={},
               timeout=timeout, queue='low')
    yield dict(name=disable_users_job, args=[],kwargs={},
               timeout=timeout, queue='low')
    yield dict(name=send_email_notifications, args=[], kwargs={},
               timeout=timeout, queue='super')


def get_maintenance_jobs():
    """Return mantainance jobs."""
    timeout = current_app.config.get('TIMEOUT')
    yield dict(name=check_failed, args=[], kwargs={},
               timeout=timeout, queue='maintenance')


def get_export_task_jobs(queue):
    """Export tasks to zip."""
    from pybossa.core import project_repo
    import pybossa.cache.projects as cached_projects
    from pybossa.pro_features import ProFeatureHandler
    feature_handler = ProFeatureHandler(current_app.config.get('PRO_FEATURES'))
    timeout = current_app.config.get('TIMEOUT')
    if feature_handler.only_for_pro('updated_exports'):
        if queue == 'high':
            projects = cached_projects.get_from_pro_user()
        else:
            projects = (p.dictize() for p in project_repo.filter_by(published=True)
                        if p.owner.pro is False)
    else:
        projects = (p.dictize() for p in project_repo.filter_by(published=True))
    for project in projects:
        project_id = project.get('id')
        job = dict(name=project_export,
                   args=[project_id], kwargs={},
                   timeout=timeout,
                   queue=queue)
        yield job


def project_export(_id):
    """Export project."""
    from pybossa.core import project_repo, json_exporter, csv_exporter
    app = project_repo.get(_id)
    if app is not None:
        # print "Export project id %d" % _id
        json_exporter.pregenerate_zip_files(app)
        csv_exporter.pregenerate_zip_files(app)


def get_project_jobs(queue):
    """Return a list of jobs based on user type."""
    from pybossa.core import project_repo
    from pybossa.cache import projects as cached_projects
    timeout = current_app.config.get('TIMEOUT')
    if queue == 'super':
        projects = cached_projects.get_from_pro_user()
    elif queue == 'high':
        projects = (p.dictize() for p in project_repo.get_all())
    else:
        projects = []
    for project in projects:
        project_id = project.get('id')
        project_short_name = project.get('short_name')
        job = dict(name=get_project_stats,
                   args=[project_id, project_short_name], kwargs={},
                   timeout=timeout,
                   queue=queue)
        yield job


def create_dict_jobs(data, function, timeout, queue='low'):
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
               AND to_date(task_run.finish_time, 'YYYY-MM-DD\THH24:MI:SS.US')
               >= NOW() - '12 month'::INTERVAL
               AND to_date(task_run.finish_time, 'YYYY-MM-DD\THH24:MI:SS.US')
               < NOW() - '3 month'::INTERVAL
               GROUP BY user_id ORDER BY user_id;''')
    results = db.slave_session.execute(sql)

    timeout = current_app.config.get('TIMEOUT')

    for row in results:

        user = User.query.get(row.user_id)

        if user.subscribed and user.restrict is False:
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
                       timeout=timeout,
                       queue=queue)
            yield job


def get_dashboard_jobs(queue='low'):  # pragma: no cover
    """Return dashboard jobs."""
    timeout = current_app.config.get('TIMEOUT')
    yield dict(name=dashboard.active_users_week, args=[], kwargs={},
               timeout=timeout, queue=queue)
    yield dict(name=dashboard.active_anon_week, args=[], kwargs={},
               timeout=timeout, queue=queue)
    yield dict(name=dashboard.draft_projects_week, args=[], kwargs={},
               timeout=timeout, queue=queue)
    yield dict(name=dashboard.published_projects_week, args=[], kwargs={},
               timeout=timeout, queue=queue)
    yield dict(name=dashboard.update_projects_week, args=[], kwargs={},
               timeout=timeout, queue=queue)
    yield dict(name=dashboard.new_tasks_week, args=[], kwargs={},
               timeout=timeout, queue=queue)
    yield dict(name=dashboard.new_task_runs_week, args=[], kwargs={},
               timeout=timeout, queue=queue)
    yield dict(name=dashboard.new_users_week, args=[], kwargs={},
               timeout=timeout, queue=queue)
    yield dict(name=dashboard.returning_users_week, args=[], kwargs={},
               timeout=timeout, queue=queue)


def get_leaderboard_jobs(queue='super'):  # pragma: no cover
    """Return leaderboard jobs."""
    timeout = current_app.config.get('TIMEOUT')
    leaderboards = current_app.config.get('LEADERBOARDS')
    if leaderboards:
        for leaderboard_key in leaderboards:
            yield dict(name=leaderboard, args=[], kwargs={'info': leaderboard_key},
                       timeout=timeout, queue=queue)
    yield dict(name=leaderboard, args=[], kwargs={},
               timeout=timeout, queue=queue)


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
    timeout = current_app.config.get('TIMEOUT')
    for row in results:
        user = User.query.get(row.id)

        if (user.subscribed and user.restrict is False):
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
                       timeout=timeout,
                       queue=queue)
            yield job


def get_autoimport_jobs(queue='low'):
    """Get autoimport jobs."""
    from pybossa.core import project_repo
    import pybossa.cache.projects as cached_projects
    from pybossa.pro_features import ProFeatureHandler
    feature_handler = ProFeatureHandler(current_app.config.get('PRO_FEATURES'))

    timeout = current_app.config.get('TIMEOUT')

    if feature_handler.only_for_pro('autoimporter'):
        projects = cached_projects.get_from_pro_user()
    else:
        projects = (p.dictize() for p in project_repo.get_all())
    for project_dict in projects:
        project = project_repo.get(project_dict['id'])
        if project.has_autoimporter():
            job = dict(name=import_tasks,
                       args=[project.id, True],
                       kwargs=project.get_autoimporter(),
                       timeout=timeout,
                       queue=queue)
            yield job


# The following are the actual jobs (i.e. tasks performed in the background)

@with_cache_disabled
def get_project_stats(_id, short_name):  # pragma: no cover
    """Get stats for project."""
    import pybossa.cache.projects as cached_projects
    import pybossa.cache.project_stats as stats
    from flask import current_app

    # cached_projects.get_project(short_name)
    stats.update_stats(_id)


@with_cache_disabled
def warm_up_stats():  # pragma: no cover
    """Background job for warming stats."""
    # print "Running on the background warm_up_stats"
    from pybossa.cache.site_stats import (n_auth_users, n_anon_users,
                                          n_tasks_site, n_total_tasks_site,
                                          n_task_runs_site,
                                          get_top5_projects_24_hours,
                                          get_top5_users_24_hours)
    current_app.logger.info('warm_up_stats - n_auth_users')
    n_auth_users()
    if not app_settings.config.get('DISABLE_ANONYMOUS_ACCESS'):
        n_anon_users()
    current_app.logger.info('warm_up_stats - n_tasks_site')
    n_tasks_site()
    current_app.logger.info('warm_up_stats - n_total_tasks_site')
    n_total_tasks_site()
    current_app.logger.info('warm_up_stats - n_task_runs_site')
    n_task_runs_site()
    current_app.logger.info('warm_up_stats - get_top5_projects_24_hours')
    get_top5_projects_24_hours()
    current_app.logger.info('warm_up_stats - get_top5_users_24_hours')
    get_top5_users_24_hours()

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
    from pybossa.core import user_repo

    def warm_project(_id, short_name, featured=False):
        if _id not in projects_cached:
            #cached_projects.get_project(short_name)
            #cached_projects.n_tasks(_id)
            #n_task_runs = cached_projects.n_task_runs(_id)
            #cached_projects.overall_progress(_id)
            #cached_projects.last_activity(_id)
            #cached_projects.n_completed_tasks(_id)
            #cached_projects.n_volunteers(_id)
            #cached_projects.browse_tasks(_id)
            #if n_task_runs >= 1000 or featured:
            #    # print ("Getting stats for %s as it has %s task runs" %
            #    #        (short_name, n_task_runs))
            stats.update_stats(_id)
            projects_cached.append(_id)

    # Cache top projects
    projects = cached_projects.get_top()
    for p in projects:
        current_app.logger.info(u'warm_project - top projects. id {} short_name{}'
            .format(p['id'], p['short_name']))
        warm_project(p['id'], p['short_name'])

    # Cache 3 pages
    to_cache = 3 * app.config['APPS_PER_PAGE']
    projects = rank(cached_projects.get_all_featured('featured'))[:to_cache]
    for p in projects:
        current_app.logger.info(u'warm_project - ranked project. id {} short_name{}'
            .format(p['id'], p['short_name']))
        warm_project(p['id'], p['short_name'], featured=True)

    # Categories
    categories = cached_cat.get_used()
    for c in categories:
        projects = rank(cached_projects.get_all(c['short_name']))[:to_cache]
        for p in projects:
            current_app.logger.info(u'warm_project - categories->rank project. id {} short_name{}'
                .format(p['id'], p['short_name']))
            warm_project(p['id'], p['short_name'])
    # Users
    current_app.logger.info('warm_project - get_leaderboard')
    users = cached_users.get_leaderboard(app.config['LEADERBOARD'])
    for user in users:
        u = user_repo.get_by_name(user['name'])
        current_app.logger.info(u'warm_project - user get_user_summary: name {}'.format(user['name']))
        cached_users.get_user_summary(user['name'])
        current_app.logger.info(u'warm_project - user projects_contributed_cached: id {}'.format(u.id))
        cached_users.projects_contributed_cached(u.id)
        current_app.logger.info(u'warm_project - user published_projects_cached: id {}'.format(u.id))
        cached_users.published_projects_cached(u.id)
        current_app.logger.info(u'warm_project - user draft_projects_cached: id {}'.format(u.id))
        cached_users.draft_projects_cached(u.id)

    return True


def get_non_updated_projects():
    """Return a list of non updated projects excluding completed ones."""
    from sqlalchemy.sql import text
    from pybossa.model.project import Project
    from pybossa.core import db
    sql = text('''SELECT id FROM project WHERE TO_DATE(updated,
                'YYYY-MM-DD\THH24:MI:SS.US') <= NOW() - '3 month':: INTERVAL
               AND contacted != True AND published = True
               AND project.id NOT IN
               (SELECT task.project_id FROM task
               WHERE task.state='completed'
               GROUP BY task.project_id)''')
    results = db.slave_session.execute(sql)
    projects = []
    for row in results:
        a = Project.query.get(row.id)
        projects.append(a)
    return projects


def warn_old_project_owners():
    """E-mail the project owners not updated in the last 3 months."""
    from smtplib import SMTPRecipientsRefused
    from pybossa.core import mail, project_repo
    from pybossa.cache.projects import clean
    from flask_mail import Message

    projects = get_non_updated_projects()

    with mail.connect() as conn:
        for project in projects:
            if (project.owner.consent and project.owner.subscribed):
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
                try:
                    conn.send(msg)
                    project.contacted = True
                    project.published = False
                    clean(project.id)
                    project_repo.update(project)
                except SMTPRecipientsRefused:
                    return False
            else:
                return False
    return True


def disable_users_job():
    from sqlalchemy.sql import text
    from pybossa.model.user import User
    from pybossa.core import db, user_repo
    from pybossa.util import generate_manage_user_email
    sql = text('''Select id
                  FROM "user"
                  WHERE current_timestamp - to_timestamp(last_login, 'YYYY-MM-DD"T"HH24:MI:SS.US') > interval '3 month'
                  AND enabled = true;
               ''')
    results = db.slave_session.execute(sql)
    users_disabled = []
    for row in results:
        user = User.query.get(row.id)
        user.enabled = False
        user_repo.update(user)
        user_info = u'name: {}, id: {}, email: {}, last_login: {}'.format(
                        user.name, user.id, user.email_addr, user.last_login)
        users_disabled.append(user_info)

    if users_disabled:
        current_app.logger.info('disable_users_job has disabled following {} users\n{}'
            .format(len(users_disabled), ', '.join(users_disabled)))
    return True


def send_mail(message_dict, mail_all=False):
    """Send email."""
    if mail_all or mail_with_enabled_users(message_dict):
        message = Message(**message_dict)
        spam = False
        for r in message_dict['recipients']:
            acc, domain = r.split('@')
            if domain in current_app.config.get('SPAM', []):
                spam = True
                break
        if not spam:
            mail.send(message)


def delete_bulk_tasks(data):
    """Delete tasks in bulk from project."""
    from sqlalchemy.sql import text
    from pybossa.core import db
    import pybossa.cache.projects as cached_projects
    from pybossa.cache.task_browse_helpers import get_task_filters

    project_id = data['project_id']
    project_name = data['project_name']
    curr_user = data['curr_user']
    coowners = data['coowners']
    current_user_fullname = data['current_user_fullname']
    force_reset = data['force_reset']
    params = {}

    # bulkdel db conn is with db user having session_replication_role
    # when bulkdel is not configured, make explict sql query to set
    # session replication role to replica
    sql_session_repl = ''
    if not 'bulkdel' in current_app.config.get('SQLALCHEMY_BINDS'):
        sql_session_repl = 'SET session_replication_role TO replica;'

    # lock tasks for given project with SELECT FOR UPDATE
    # create temp table with all tasks to be deleted
    # during transaction, disable constraints check with session_replication_role
    # delete rows from child talbes first and then from parent
    if not force_reset:
        """Delete only tasks that have no results associated."""
        sql = text('''
                BEGIN;
                SELECT task_id FROM counter WHERE project_id=:project_id FOR UPDATE;
                SELECT task_id FROM task_run WHERE project_id=:project_id FOR UPDATE;
                SELECT id FROM task WHERE project_id=:project_id FOR UPDATE;

                {}

                CREATE TEMP TABLE to_delete ON COMMIT DROP AS (
                    SELECT task.id as id FROM task WHERE project_id=:project_id
                    AND task.id NOT IN
                    (SELECT task_id FROM result
                    WHERE result.project_id=:project_id
                    GROUP BY result.task_id)
                );

                DELETE FROM counter WHERE project_id=:project_id
                        AND task_id IN (SELECT id FROM to_delete);
                DELETE FROM task_run WHERE project_id=:project_id
                        AND task_id IN (SELECT id FROM to_delete);
                DELETE FROM task WHERE project_id=:project_id
                        AND id IN (SELECT id FROM to_delete);

                COMMIT;
                '''.format(sql_session_repl))
        msg = ("Tasks and taskruns with no associated results have been "
               "deleted from project {0} by {1}"
               .format(project_name, current_user_fullname))
    else:
        args = data.get('filters', {})
        conditions, params = get_task_filters(args)
        sql = text('''
                BEGIN;
                SELECT task_id FROM counter WHERE project_id=:project_id FOR UPDATE;
                SELECT task_id FROM result WHERE project_id=:project_id FOR UPDATE;
                SELECT task_id FROM task_run WHERE project_id=:project_id FOR UPDATE;
                SELECT id FROM task WHERE project_id=:project_id FOR UPDATE;

                {}

                CREATE TEMP TABLE to_delete ON COMMIT DROP AS (
                    SELECT task.id as id,
                    coalesce(ct, 0) as n_task_runs, task.n_answers, ft,
                    priority_0, task.created
                    FROM task LEFT OUTER JOIN
                    (SELECT task_id, CAST(COUNT(id) AS FLOAT) AS ct,
                    MAX(finish_time) as ft FROM task_run
                    WHERE project_id=:project_id GROUP BY task_id) AS log_counts
                    ON task.id=log_counts.task_id
                    WHERE task.project_id=:project_id {}
                );

                DELETE FROM counter WHERE project_id=:project_id
                        AND task_id IN (SELECT id FROM to_delete);
                DELETE FROM result WHERE project_id=:project_id
                       AND task_id in (SELECT id FROM to_delete);
                DELETE FROM task_run WHERE project_id=:project_id
                       AND task_id in (SELECT id FROM to_delete);
                DELETE FROM task WHERE task.project_id=:project_id
                       AND id in (SELECT id FROM to_delete);

                COMMIT;
                '''.format(sql_session_repl, conditions))
        msg = ("Tasks, taskruns and results associated have been "
               "deleted from project {0} as requested by {1}"
               .format(project_name, current_user_fullname))
    db.bulkdel_session.execute(sql, dict(project_id=project_id, **params))
    cached_projects.clean_project(project_id)
    subject = 'Tasks deletion from %s' % project_name
    body = 'Hello,\n\n' + msg + '\n\nThe %s team.'\
        % current_app.config.get('BRAND')

    recipients = [curr_user]
    for user in coowners:
        recipients.append(user.email_addr)

    mail_dict = dict(recipients=recipients, subject=subject, body=body)
    send_mail(mail_dict)


def send_email_notifications():
    from pybossa.core import sentinel
    from pybossa.cache import projects as cached_projects
    from pybossa.core import project_repo
    from pybossa.sched import Schedulers

    redis_conn = sentinel.master
    project_set = redis_conn.hgetall('updated_project_ids') or {}
    for project_id, timestamp in project_set.iteritems():
        project = project_repo.get(project_id)
        redis_conn.hdel('updated_project_ids', project_id)
        if not project.email_notif:
            continue
        user_emails = []
        if cached_projects.get_project_scheduler(project_id) == Schedulers.user_pref:
            user_emails = user_repo.get_user_pref_recent_contributor_emails(project_id, timestamp)
        else:
            if cached_projects.overall_progress(project_id) != 100:
                user_emails = user_repo.get_recent_contributor_emails(project_id)

        if user_emails:
            recipients = []
            for email_addr in user_emails:
                if email_addr not in recipients:
                    recipients.append(email_addr)
            subject = (u'New Tasks have been imported to {}'.format(project.name))
            body = u'Hello,\n\nThere have been new tasks uploaded to the previously finished project, {0}. ' \
                   u'\nLog on to {1} to complete any available tasks.' \
                .format(project.name, current_app.config.get('BRAND'))
            mail_dict = dict(recipients=recipients, subject=subject, body=body)
            send_mail(mail_dict)
    return True


def _num_tasks_imported(project_id):
    from sqlalchemy.sql import text
    from pybossa.core import db
    sql = text('''
        SELECT COUNT(*) FROM task WHERE
        project_id=:project_id AND
            clock_timestamp()
                - to_timestamp(task.created, 'YYYY-MM-DD"T"HH24:MI:SS.US')
            < INTERVAL ':seconds seconds'
        ''')
    params = dict(seconds=IMPORT_TASKS_TIMEOUT + 10, project_id=project_id)
    return db.session.execute(sql, params).scalar()


def import_tasks(project_id, current_user_fullname, from_auto=False, **form_data):
    """Import tasks for a project."""
    from pybossa.core import project_repo, user_repo
    import pybossa.cache.projects as cached_projects

    project = project_repo.get(project_id)
    recipients = []
    for user in user_repo.get_users(project.owners_ids):
        recipients.append(user.email_addr)

    try:
        with current_app.test_request_context():
            report = importer.create_tasks(task_repo, project, **form_data)
    except JobTimeoutException:
        from pybossa.core import db
        db.session.rollback()
        n_tasks = _num_tasks_imported(project_id)
        subject = 'Your import task has timed out'
        body = '\n'.join(
            ['Hello,\n',
             'Import task to your project {} by {} failed because the file was too large.',
             'It was able to process approximately {} tasks.',
             'Please break up your task upload into smaller CSV files.',
             'Thank you,\n',
             u'The {} team.']).format(project.name, current_user_fullname,
                                     n_tasks, current_app.config.get('BRAND'))
        mail_dict = dict(recipients=recipients, subject=subject, body=body)
        send_mail(mail_dict)
        raise
    except Exception as e:
        msg = (u'Import tasks to your project {} by {} failed. Error: {}'
               .format(project.name, current_user_fullname, str(e)))
        subject = 'Tasks Import to your project %s' % project.name
        body = (u'Hello,\n\n{0}\n\nPlease contact {1} administrator,\nThe {1} team.'
                .format(msg, current_app.config.get('BRAND')))
        mail_dict = dict(recipients=recipients, subject=subject, body=body)
        send_mail(mail_dict)
        raise

    cached_projects.delete_browse_tasks(project_id)
    if from_auto:
        form_data['last_import_meta'] = report.metadata
        project.set_autoimporter(form_data)
        project_repo.save(project)
    msg = report.message + u' to your project {0} by {1}'.format(project.name, current_user_fullname)

    subject = 'Tasks Import to your project %s' % project.name
    body = 'Hello,\n\n' + msg + '\n\nAll the best,\nThe %s team.'\
        % current_app.config.get('BRAND')
    mail_dict = dict(recipients=recipients, subject=subject, body=body)
    send_mail(mail_dict)
    return msg


def export_tasks(current_user_email_addr, short_name,
                 ty, expanded, filetype, filters=None, disclose_gold=False):
    """Export tasks/taskruns from a project."""
    from pybossa.core import (task_csv_exporter, task_json_exporter,
                              project_repo)
    import pybossa.exporter.consensus_exporter as export_consensus

    project = project_repo.get_by_shortname(short_name)

    try:
        # Export data and upload .zip file locally
        if ty == 'consensus':
            export_fn = getattr(export_consensus,
                                'export_consensus_{}'.format(filetype))
        elif filetype == 'json':
            export_fn = task_json_exporter.make_zip
        elif filetype == 'csv':
            export_fn = task_csv_exporter.make_zip
        else:
            export_fn = None

        mail_dict = dict(recipients=[current_user_email_addr])
        # Construct message
        if export_fn is not None:
            mail_dict['subject'] = u'Data exported for your project: {0}'.format(project.name)
            with export_fn(project, ty, expanded, filters, disclose_gold) as fp:
                filename = fp.filename
                content = fp.read()
            data = project.info
            bucket_name = current_app.config.get('EXPORT_BUCKET')
            max_size = current_app.config.get('EXPORT_MAX_SIZE', float('Inf'))

            if len(content) > max_size and bucket_name:
                conn = create_connection(**current_app.config.get('S3_EXPORT_CONN', {}))
                bucket = conn.get_bucket(bucket_name, validate=False)
                timestamp = datetime.utcnow().isoformat()
                key = bucket.new_key('{}-{}'.format(timestamp, filename))
                key.set_contents_from_string(content)
                url = key.generate_url(current_app.config.get('EXPORT_EXPIRY', 12 * 3600))
                msg = u'<p>You can download your file <a href="{}">here</a>.</p>'.format(url)
            else:
                msg = u'<p>Your exported data is attached.</p>'
                mail_dict['attachments'] = [Attachment(filename, "application/zip", content)]
        else:
            # Failure email
            mail_dict['subject'] = u'Data export failed for your project: {0}'.format(project.name)
            msg = u'<p>There was an issue with your export. ' + \
                  u'Please try again or report this issue ' + \
                  u'to a {0} administrator.</p>'
            msg = msg.format(current_app.config.get('BRAND'))

        body = u'<p>Hello,</p>' + msg + '<p>The {0} team.</p>'
        body = body.format(current_app.config.get('BRAND'))
        mail_dict['html'] = body
        message = Message(**mail_dict)
        mail.send(message)
        job_response = u'{0} {1} file was successfully exported for: {2}'
        return job_response.format(
                ty.capitalize(), filetype.upper(), project.name)
    except:
        current_app.logger.exception(
                u'Export email failed - Project: {0}'
                .format(project.name))
        subject = u'Email delivery failed for your project: {0}'.format(project.name)
        msg = u'There was an error when attempting to deliver your data export via email.'
        body = u'Hello,\n\n' + msg + u'\n\nThe {0} team.'
        body = body.format(current_app.config.get('BRAND'))
        mail_dict = dict(recipients=[current_user_email_addr],
                         subject=subject,
                         body=body)
        message = Message(**mail_dict)
        mail.send(message)
        raise


def webhook(url, payload=None, oid=None, rerun=False):
    """Post to a webhook."""
    from flask import current_app
    from readability.readability import Document
    try:
        import json
        from pybossa.core import sentinel, webhook_repo, project_repo
        project = project_repo.get(payload['project_id'])
        headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        if oid:
            webhook = webhook_repo.get(oid)
        else:
            webhook = Webhook(project_id=payload['project_id'],
                              payload=payload)
        if url:
            params = dict()
            if rerun:
                params['rerun'] = True
            response = requests.post(url, params=params,
                                     data=json.dumps(payload),
                                     headers=headers)
            webhook.response = Document(response.text).summary()
            webhook.response_status_code = response.status_code
        else:
            raise requests.exceptions.ConnectionError('Not URL')
        if oid:
            webhook_repo.update(webhook)
            webhook = webhook_repo.get(oid)
        else:
            webhook_repo.save(webhook)
    except requests.exceptions.ConnectionError:
        webhook.response = 'Connection Error'
        webhook.response_status_code = None
        webhook_repo.save(webhook)
    finally:
        if project.published and webhook.response_status_code != 200 and current_app.config.get('ADMINS'):
            subject = "Broken: %s webhook failed" % project.name
            body = 'Sorry, but the webhook failed'
            mail_dict = dict(recipients=current_app.config.get('ADMINS'),
                             subject=subject, body=body, html=webhook.response)
            send_mail(mail_dict)
    if current_app.config.get('SSE'):
        publish_channel(sentinel, payload['project_short_name'],
                        data=webhook.dictize(), type='webhook',
                        private=True)
    return webhook


def notify_blog_users(blog_id, project_id, queue='high'):
    """Send email with new blog post."""
    from sqlalchemy.sql import text
    from pybossa.core import db
    from pybossa.core import blog_repo
    from pybossa.pro_features import ProFeatureHandler

    blog = blog_repo.get(blog_id)
    users = 0
    feature_handler = ProFeatureHandler(current_app.config.get('PRO_FEATURES'))
    only_pros = feature_handler.only_for_pro('notify_blog_updates')
    timeout = current_app.config.get('TIMEOUT')
    if blog.project.featured or (blog.project.owner.pro or not only_pros):
        sql = text('''
                   SELECT email_addr, name from "user", task_run
                   WHERE task_run.project_id=:project_id
                   AND task_run.user_id="user".id
                   AND "user".subscribed=true
                   AND "user".restrict=false
                   GROUP BY email_addr, name, subscribed;
                   ''')
        results = db.slave_session.execute(sql, dict(project_id=project_id))
        for row in results:
            subject = "Project Update: %s by %s" % (blog.project.name,
                                                    blog.project.owner.fullname)
            body = render_template('/account/email/blogupdate.md',
                                   user_name=row.name,
                                   blog=blog,
                                   config=current_app.config)
            html = render_template('/account/email/blogupdate.html',
                                   user_name=row.name,
                                   blog=blog,
                                   config=current_app.config)
            mail_dict = dict(recipients=[row.email_addr],
                             subject=subject,
                             body=body,
                             html=html)

            job = dict(name=send_mail,
                       args=[mail_dict],
                       kwargs={},
                       timeout=timeout,
                       queue=queue)
            enqueue_job(job)
            users += 1
    msg = "%s users notified by email" % users
    return msg


def get_weekly_stats_update_projects():
    """Return email jobs with weekly stats update for project owner."""
    from sqlalchemy.sql import text
    from pybossa.core import db
    from pybossa.pro_features import ProFeatureHandler

    feature_handler = ProFeatureHandler(current_app.config.get('PRO_FEATURES'))
    only_pros = feature_handler.only_for_pro('project_weekly_report')
    only_pros_sql = 'AND "user".pro=true' if only_pros else ''
    send_emails_date = current_app.config.get('WEEKLY_UPDATE_STATS')
    today = datetime.today().strftime('%A').lower()
    timeout = current_app.config.get('TIMEOUT')
    if today.lower() == send_emails_date.lower():
        sql = text('''
                   SELECT project.id
                   FROM project, "user", task
                   WHERE "user".id=project.owner_id %s
                   AND "user".subscribed=true
                   AND "user".restrict=false
                   AND task.project_id=project.id
                   AND task.state!='completed'
                   UNION
                   SELECT project.id
                   FROM project
                   WHERE project.featured=true;
                   ''' % only_pros_sql)
        results = db.slave_session.execute(sql)
        for row in results:
            job = dict(name=send_weekly_stats_project,
                       args=[row.id],
                       kwargs={},
                       timeout=timeout,
                       queue='low')
            yield job


def send_weekly_stats_project(project_id):
    from pybossa.cache.project_stats import update_stats, get_stats
    from pybossa.core import project_repo
    from datetime import datetime
    project = project_repo.get(project_id)
    if project.owner.subscribed is False or project.owner.restrict:
        return "Owner does not want updates by email"
    update_stats(project_id)
    dates_stats, hours_stats, users_stats = get_stats(project_id,
                                                      period='1 week')
    subject = "Weekly Update: %s" % project.name

    timeout = current_app.config.get('TIMEOUT')

    # Max number of completed tasks
    n_completed_tasks = 0
    xy = zip(*dates_stats[3]['values'])
    n_completed_tasks = max(xy[1])
    # Most active day
    xy = zip(*dates_stats[0]['values'])
    active_day = [xy[0][xy[1].index(max(xy[1]))], max(xy[1])]
    active_day[0] = datetime.fromtimestamp(active_day[0]/1000).strftime('%A')
    body = render_template('/account/email/weeklystats.md',
                           project=project,
                           dates_stats=dates_stats,
                           hours_stats=hours_stats,
                           users_stats=users_stats,
                           n_completed_tasks=n_completed_tasks,
                           active_day=active_day,
                           config=current_app.config)
    html = render_template('/account/email/weeklystats.html',
                           project=project,
                           dates_stats=dates_stats,
                           hours_stats=hours_stats,
                           users_stats=users_stats,
                           active_day=active_day,
                           n_completed_tasks=n_completed_tasks,
                           config=current_app.config)
    mail_dict = dict(recipients=[project.owner.email_addr],
                     subject=subject,
                     body=body,
                     html=html)

    job = dict(name=send_mail,
               args=[mail_dict],
               kwargs={},
               timeout=timeout,
               queue='high')
    enqueue_job(job)


def news():
    """Get news from different ATOM RSS feeds."""
    import feedparser
    from pybossa.core import sentinel
    from pybossa.news import get_news, notify_news_admins, FEED_KEY
    try:
        import cPickle as pickle
    except ImportError:  # pragma: no cover
        import pickle
    urls = ['https://github.com/Scifabric/pybossa/releases.atom',
            'http://scifabric.com/blog/all.atom.xml']
    score = 0
    notify = False
    if current_app.config.get('NEWS_URL'):
        urls += current_app.config.get('NEWS_URL')
    for url in urls:
        d = feedparser.parse(url)
        tmp = get_news(score)
        if (d.entries and (len(tmp) == 0)
           or (tmp[0]['updated'] != d.entries[0]['updated'])):
            mapping = dict()
            mapping[pickle.dumps(d.entries[0])] = float(score)
            sentinel.master.zadd(FEED_KEY, mapping)
            notify = True
        score += 1
    if notify:
        notify_news_admins()

def check_failed():
    """Check the jobs that have failed and requeue them."""
    from rq import Queue, get_failed_queue, requeue_job
    from pybossa.core import sentinel

    fq = get_failed_queue()
    job_ids = fq.job_ids
    count = len(job_ids)
    FAILED_JOBS_RETRIES = current_app.config.get('FAILED_JOBS_RETRIES')
    for job_id in job_ids:
        KEY = 'pybossa:job:failed:%s' % job_id
        job = fq.fetch_job(job_id)
        if sentinel.slave.exists(KEY):
            sentinel.master.incr(KEY)
        else:
            ttl = current_app.config.get('FAILED_JOBS_MAILS')*24*60*60
            sentinel.master.setex(KEY, ttl, 1)
        if int(sentinel.slave.get(KEY)) < FAILED_JOBS_RETRIES:
            requeue_job(job_id)
        else:
            KEY = 'pybossa:job:failed:mailed:%s' % job_id
            if (not sentinel.slave.exists(KEY) and
                    current_app.config.get('ADMINS')):
                subject = "JOB: %s has failed more than 3 times" % job_id
                body = "Please, review the background jobs of your server."
                body += "\n This is the trace error\n\n"
                body += "------------------------------\n\n"
                body += job.exc_info
                mail_dict = dict(recipients=current_app.config.get('ADMINS'),
                                 subject=subject, body=body)
                send_mail(mail_dict)
                ttl = current_app.config.get('FAILED_JOBS_MAILS')*24*60*60
                sentinel.master.setex(KEY, ttl, 1)
    if count > 0:
        return "JOBS: %s You have failed the system." % job_ids
    else:
        return "You have not failed the system"


def push_notification(project_id, **kwargs):
    """Send push notification."""
    from pybossa.core import project_repo
    project = project_repo.get(project_id)
    if project.info.get('onesignal'):
        app_id = current_app.config.get('ONESIGNAL_APP_ID')
        api_key = current_app.config.get('ONESIGNAL_API_KEY')
        client = PybossaOneSignal(app_id=app_id, api_key=api_key)
        filters = [{"field": "tag", "key": project_id, "relation": "exists"}]
        return client.push_msg(contents=kwargs['contents'],
                               headings=kwargs['headings'],
                               launch_url=kwargs['launch_url'],
                               web_buttons=kwargs['web_buttons'],
                               filters=filters)


def mail_project_report(info, current_user_email_addr):
    from pybossa.core import project_csv_exporter

    try:
        zipfile = None
        filename = project_csv_exporter.zip_name(info)
        subject = '{} project report'.format(current_app.config['BRAND'])
        msg = 'Your exported data is attached.'

        body = 'Hello,\n\n{}\n\nThe {} team.'
        body = body.format(msg, current_app.config.get('BRAND'))
        mail_dict = dict(recipients=[current_user_email_addr],
                         subject=subject,
                         body=body)

        container = 'user_{}'.format(info['user_id'])
        zipfile = project_csv_exporter.generate_zip_files(info)
        with open(zipfile) as fp:
            attachment = Attachment(filename, "application/zip",
                                    fp.read())
        mail_dict['attachments'] = [attachment]
    except Exception:
        current_app.logger.exception('Error in mail_project_report')
        subject = 'Error in {} project report'.format(current_app.config['BRAND'])
        msg = 'An error occurred while exporting your report.'

        body = 'Hello,\n\n{}\n\nThe {} team.'
        body = body.format(msg, current_app.config.get('BRAND'))
        mail_dict = dict(recipients=[current_user_email_addr],
                         subject=subject,
                         body=body)
        send_mail(mail_dict)
        raise
    finally:
        if zipfile:
            os.unlink(zipfile)

    send_mail(mail_dict)


def delete_account(user_id, admin_addr, **kwargs):
    """Delete user account from the system."""
    from pybossa.core import (user_repo, uploader)
    user = user_repo.get(user_id)

    container = "user_%s" % user.id
    if user.info.get('avatar'):
        uploader.delete_file(user.info['avatar'], container)

    email = user.email_addr
    if current_app.config.get('MAILCHIMP_API_KEY'):
        from pybossa.core import newsletter
        newsletter.init_app(current_app)
        mailchimp_deleted = newsletter.delete_user(email)
    else:
        mailchimp_deleted = True
    brand = current_app.config.get('BRAND')
    user_repo.delete_data(user)
    subject = '[%s]: Your account has been deleted' % brand
    body = """Hi,\n Your account and personal data has been deleted from %s.""" % brand
    if not mailchimp_deleted:
        body += '\nWe could not delete your Mailchimp account, please contact us to fix this issue.'
    if current_app.config.get('DISQUS_SECRET_KEY'):
        body += '\nDisqus does not provide an API method to delete your account. You will have to do it by hand yourself in the disqus.com site.'
    recipients = [email]
    if current_app.config.get('ADMINS'):
        for em in current_app.config.get('ADMINS'):
            recipients.append(em)
    bcc = [admin_addr]
    mail_dict = dict(recipients=recipients, bcc=bcc, subject=subject, body=body)
    send_mail(mail_dict, mail_all=True)


def export_userdata(user_id, admin_addr, **kwargs):
    from pybossa.core import (user_repo, uploader)
    from flask import current_app, url_for
    json_exporter = JsonExporter()
    user = user_repo.get(user_id)
    user_data = user.dictize()
    del user_data['passwd_hash']

    buffer = StringIO()
    with ZipFile(buffer, 'w') as zf:
        zf.writestr('personal_data.json', json.dumps(user_data))
    buffer.seek(0)
    attachments = [Attachment('personal_data.zip', 'application/zip', buffer.read())]
    body = render_template('/account/email/exportdata.md',
                           user=user.dictize(),
                           personal_data_link=None,
                           config=current_app.config)

    html = render_template('/account/email/exportdata.html',
                           user=user.dictize(),
                           personal_data_link=None,
                           config=current_app.config)
    subject = 'Your personal data'
    bcc = [admin_addr]
    mail_dict = dict(recipients=[user.email_addr],
                     bcc=bcc,
                     subject=subject,
                     body=body,
                     html=html,
                     attachments=attachments)
    send_mail(mail_dict)


def delete_file(fname, container):
    """Delete file."""
    from pybossa.core import uploader
    return uploader.delete_file(fname, container)


def get_management_dashboard_stats(user_email):
    """Rebuild management dashboard stats, notify user about its availability"""
    project_chart = site_stats.project_chart()
    category_chart = site_stats.category_chart()
    task_chart = site_stats.task_chart()
    submission_chart = site_stats.submission_chart()

    timed_stats_funcs = [
        site_stats.number_of_active_jobs,
        site_stats.number_of_created_jobs,
        site_stats.number_of_created_tasks,
        site_stats.number_of_completed_tasks,
        site_stats.avg_time_to_complete_task,
        site_stats.number_of_active_users,
        site_stats.categories_with_new_projects
    ]

    current_stats_funcs = [
        site_stats.avg_task_per_job,
        site_stats.tasks_per_category
    ]

    timed_stats = OrderedDict()
    for func in timed_stats_funcs:
        timed_stats[func.__doc__] = OrderedDict()
        for days in [30, 60, 90, 350, 'all']:
            timed_stats[func.__doc__][days] = func(days)

    current_stats = OrderedDict((func.__doc__, func())
                                for func in current_stats_funcs)

    subject = 'Management Dashboard Statistics'
    msg = 'Management dashboard statistics is now available. It can be accessed by refreshing management dashboard page.'
    body = (u'Hello,\n\n{}\nThe {} team.'
            .format(msg, current_app.config.get('BRAND')))
    mail_dict = dict(recipients=[user_email], subject=subject, body=body)
    send_mail(mail_dict)


def export_all_users(fmt, email_addr):
    exportable_attributes = ('id', 'name', 'fullname', 'email_addr', 'locale',
                             'created', 'admin', 'subadmin', 'enabled', 'languages',
                             'locations', 'work_hours_from', 'work_hours_to',
                             'timezone', 'type_of_user', 'additional_comments',
                             'total_projects_contributed', 'completed_tasks',
                             'percentage_tasks_completed', 'first_submission_date',
                             'last_submission_date', 'avg_time_per_task', 'consent',
                             'restrict')

    def respond_json():
        return gen_json()

    def gen_json():
        users = get_users_for_report()
        jdata = json.dumps(users)
        return jdata

    def respond_csv():
        out = StringIO()
        writer = UnicodeWriter(out)
        tmp = 'attachment; filename=all_users.csv'
        return gen_csv(out, writer, write_user)

    def gen_csv(out, writer, write_user):
        add_headers(writer)
        users = get_users_for_report()
        for user in users:
            write_user(writer, user)
        return out.getvalue()

    def write_user(writer, user):
        values = [user[attr] for attr in exportable_attributes]
        writer.writerow(values)

    def add_headers(writer):
        writer.writerow(exportable_attributes)

    try:
        data = {"json": respond_json, "csv": respond_csv}[fmt]()
        attachment = Attachment(
            'user_export.{}'.format(fmt),
            'application/{}'.format(fmt),
            data
        )
        mail_dict = {
            'recipients': [email_addr],
            'subject': 'User Export',
            'body': 'Your exported data is attached.',
            'attachments': [attachment]
        }
    except Exception as e:
        mail_dict = {
            'recipients': [email_addr],
            'subject': 'User Export Failed',
            'body': 'User export failed, {}'.format(str(e))
        }
        raise
    finally:
        send_mail(mail_dict)
