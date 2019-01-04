# -*- coding: utf8 -*-
# This file is part of PYBOSSA.
#
# Copyright (C) 2017 Scifabric LTD.
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
"""Cache module for users."""
from sqlalchemy.sql import text
from sqlalchemy.exc import ProgrammingError
from pybossa.core import db, timeouts
from pybossa.cache import cache, memoize, delete_memoized
from pybossa.util import pretty_date, exists_materialized_view
from pybossa.model.user import User
from pybossa.cache.projects import overall_progress, n_tasks, n_volunteers
from pybossa.model.project import Project
from pybossa.leaderboard.data import get_leaderboard as gl
from pybossa.leaderboard.jobs import leaderboard as lb


session = db.slave_session


def get_leaderboard(n, user_id=None, window=0, info=None):
    """Return the top n users with their rank."""
    try:
        return gl(top_users=n, user_id=user_id, window=window, info=info)
    except ProgrammingError:
        db.session.rollback()
        lb(info=info)
        return gl(top_users=n, user_id=user_id, window=window, info=info)


@memoize(timeout=timeouts.get('USER_TIMEOUT'))
def get_user_summary(name, current_user=None):
    """Return user summary."""
    sql = text('''
               SELECT "user".id, "user".name, "user".fullname, "user".created,
               "user".api_key, "user".twitter_user_id, "user".facebook_user_id,
               "user".google_user_id, "user".info, "user".admin,
               "user".locale,
               "user".email_addr, COUNT(task_run.user_id) AS n_answers,
               "user".valid_email, "user".confirmation_email_sent, 
               "user".restrict
               FROM "user"
               LEFT OUTER JOIN task_run ON "user".id=task_run.user_id
               WHERE "user".name=:name
               GROUP BY "user".id;
               ''')
    results = session.execute(sql, dict(name=name))
    user = dict()
    for row in results:
        user = dict(id=row.id, name=row.name, fullname=row.fullname,
                    created=row.created, api_key=row.api_key,
                    twitter_user_id=row.twitter_user_id,
                    google_user_id=row.google_user_id,
                    facebook_user_id=row.facebook_user_id,
                    info=row.info, admin=row.admin,
                    locale=row.locale,
                    email_addr=row.email_addr, n_answers=row.n_answers,
                    valid_email=row.valid_email,
                    confirmation_email_sent=row.confirmation_email_sent,
                    restrict=row.restrict,
                    registered_ago=pretty_date(row.created))
    if user:
        rank_score = rank_and_score(user['id'])
        user['rank'] = rank_score['rank']
        user['score'] = rank_score['score']
        user['total'] = get_total_users()
        if user['restrict']:
            if (current_user and
                current_user.is_authenticated and
               (current_user.id == user['id'])):
                return user
            else:
                return None
        else:
            return user
    else:  # pragma: no cover
        return None


@memoize(timeout=timeouts.get('USER_TIMEOUT'))
def public_get_user_summary(name):
    """Sanitize user summary for public usage"""
    private_user = get_user_summary(name)
    public_user = None
    if private_user is not None:
        u = User()
        public_user = u.to_public_json(data=private_user)
    return public_user


@memoize(timeout=timeouts.get('USER_TIMEOUT'))
def rank_and_score(user_id):
    """Return rank and score for a user."""
    if exists_materialized_view(db, 'users_rank') is False:
        lb()
    sql = text('''SELECT * from users_rank WHERE id=:user_id''')
    results = session.execute(sql, dict(user_id=user_id))
    rank_and_score = dict(rank=None, score=None)
    for row in results:
        rank_and_score['rank'] = row.rank
        rank_and_score['score'] = row.score
    return rank_and_score


def projects_contributed(user_id, order_by='name'):
    """Return projects that user_id has contributed to."""
    sql = text('''
               WITH projects_contributed as
                    (SELECT project_id, MAX(finish_time) as last_contribution  FROM task_run
                     WHERE user_id=:user_id GROUP BY project_id)
               SELECT * FROM project, projects_contributed
               WHERE project.id=projects_contributed.project_id ORDER BY {} DESC;
               '''.format(order_by))
    results = session.execute(sql, dict(user_id=user_id))
    projects_contributed = []
    for row in results:
        project = dict(row)
        project['n_tasks'] = n_tasks(row.id)
        project['n_volunteers'] = n_volunteers(row.id)
        project['overall_progress'] = overall_progress(row.id)
        projects_contributed.append(project)
    return projects_contributed


@memoize(timeout=timeouts.get('USER_TIMEOUT'))
def projects_contributed_cached(user_id, order_by='name'):
    """Return projects contributed too (cached version)."""
    return projects_contributed(user_id, order_by='name')


def public_projects_contributed(user_id):
    """Return projects that user_id has contributed to. Public information only"""
    unsanitized_projects = projects_contributed(user_id)
    public_projects = []
    if unsanitized_projects:
        p = Project()
        for project in unsanitized_projects:
            public_project = p.to_public_json(data=project)
            public_projects.append(public_project)
    return public_projects


@memoize(timeout=timeouts.get('USER_TIMEOUT'))
def public_projects_contributed_cached(user_id):
    """Return projects contributed too (cached version)."""
    return public_projects_contributed(user_id)


def published_projects(user_id):
    """Return published projects for user_id."""
    sql = text('''
               SELECT *
               FROM project
               WHERE project.published=true
               AND :user_id = ANY (project.owners_ids::int[]);
               ''')
    projects_published = []
    results = session.execute(sql, dict(user_id=user_id))
    for row in results:
        project = dict(row)
        project['n_tasks'] = n_tasks(row.id)
        project['n_volunteers'] = n_volunteers(row.id)
        project['overall_progress'] = overall_progress(row.id)
        projects_published.append(project)
    return projects_published


@memoize(timeout=timeouts.get('USER_TIMEOUT'))
def published_projects_cached(user_id):
    """Return published projects (cached version)."""
    return published_projects(user_id)


def public_published_projects(user_id):
    """Return projects that user_id has contributed to. Public information only"""
    unsanitized_projects = published_projects(user_id)
    public_projects = []
    if unsanitized_projects:
        p = Project()
        for project in unsanitized_projects:
            public_project = p.to_public_json(data=project)
            public_projects.append(public_project)
    return public_projects


@memoize(timeout=timeouts.get('USER_TIMEOUT'))
def public_published_projects_cached(user_id):
    """Return published projects (cached version)."""
    return public_published_projects(user_id)


def draft_projects(user_id):
    """Return draft projects for user_id."""
    sql = text('''
               SELECT *
               FROM project
               WHERE project.published=false
               AND :user_id = ANY (project.owners_ids::int[]);
               ''')
    projects_draft = []
    results = session.execute(sql, dict(user_id=user_id))
    for row in results:
        project = dict(row)
        project['n_tasks'] = n_tasks(row.id)
        project['n_volunteers'] = n_volunteers(row.id)
        project['overall_progress'] = overall_progress(row.id)
        projects_draft.append(project)
    return projects_draft


@memoize(timeout=timeouts.get('USER_TIMEOUT'))
def draft_projects_cached(user_id):
    """Return draft projects (cached version)."""
    return draft_projects(user_id)


@cache(timeout=timeouts.get('USER_TOTAL_TIMEOUT'),
       key_prefix="site_total_users")
def get_total_users():
    """Return total number of users in the server."""
    count = User.query.count()
    return count


@memoize(timeout=timeouts.get('USER_TIMEOUT'))
def get_users_page(page, per_page=24):
    """Return users with a paginator."""
    offset = (page - 1) * per_page
    sql = text('''SELECT "user".id, "user".name,
               "user".fullname, "user".email_addr,
               "user".created, "user".info, COUNT(task_run.id) AS task_runs
               FROM task_run, "user"
               WHERE "user".id=task_run.user_id GROUP BY "user".id
               ORDER BY "user".created DESC LIMIT :limit OFFSET :offset''')
    results = session.execute(sql, dict(limit=per_page, offset=offset))
    accounts = []

    u = User()

    for row in results:
        user = dict(id=row.id, name=row.name, fullname=row.fullname,
                    email_addr=row.email_addr, created=row.created,
                    task_runs=row.task_runs, info=row.info,
                    registered_ago=pretty_date(row.created))
        tmp = u.to_public_json(data=user)
        accounts.append(tmp)
    return accounts


def delete_user_summary_id(oid):
    """Delete from cache the user summary."""
    user = db.session.query(User).get(oid)
    delete_memoized(get_user_summary, user.name)


def delete_user_summary(name):
    """Delete from cache the user summary."""
    delete_memoized(get_user_summary, name)


@memoize(timeout=timeouts.get('APP_TIMEOUT'))
def get_project_report_userdata(project_id):
    """Return users details who contributed to a particular project."""
    if project_id is None:
        return None

    total_tasks = n_tasks(project_id)
    sql = text(
            '''
            SELECT id as u_id, name, fullname,
            (SELECT count(id) FROM task_run WHERE user_id = u.id AND project_id=:project_id) AS completed_tasks,
            ((SELECT count(id) FROM task_run WHERE user_id = u.id AND project_id =:project_id) * 100 / :total_tasks) AS percent_completed_tasks,
            (SELECT min(finish_time) FROM task_run WHERE user_id = u.id AND project_id=:project_id) AS first_submission_date,
            (SELECT max(finish_time) FROM task_run WHERE user_id = u.id AND project_id=:project_id) AS last_submission_date,
            (SELECT coalesce(AVG(to_timestamp(finish_time, 'YYYY-MM-DD"T"HH24-MI-SS.US') -
            to_timestamp(created, 'YYYY-MM-DD"T"HH24-MI-SS.US')), interval '0s')
            FROM task_run WHERE user_id = u.id AND project_id=:project_id) AS avg_time_per_task
            FROM public.user u WHERE id IN
            (SELECT DISTINCT user_id FROM task_run tr GROUP BY project_id, user_id HAVING project_id=:project_id);
            ''')
    results = session.execute(sql, dict(project_id=project_id, total_tasks=total_tasks))
    users_report = [
        [row.u_id, row.name, row.fullname,
         row.completed_tasks, row.percent_completed_tasks,
         row.first_submission_date, row.last_submission_date,
         round(row.avg_time_per_task.total_seconds() / 60, 2)]
         for row in results]
    return users_report


@memoize(timeout=timeouts.get('APP_TIMEOUT'))
def get_user_pref_metadata(name):
    sql = text("""
    SELECT info->'metadata', user_pref FROM public.user WHERE name=:name;
    """)

    cursor = session.execute(sql, dict(name=name))
    row = cursor.fetchone()
    upref_mdata = row[0] or {}
    upref_mdata.update(row[1] or {})
    return upref_mdata


def delete_user_pref_metadata(name):
    delete_memoized(get_user_pref_metadata, name)
