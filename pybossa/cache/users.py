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
from pybossa.core import db, timeouts
from pybossa.cache import cache, memoize, delete_memoized
from pybossa.util import pretty_date
from pybossa.model.user import User
from pybossa.model.task_run import TaskRun
from pybossa.cache.projects import overall_progress, n_tasks, n_volunteers
from pybossa.model.project import Project


session = db.slave_session


@memoize(timeout=timeouts.get('USER_TIMEOUT'))
def get_leaderboard(n, user_id=None):
    """Return the top n users with their rank."""
    sql = text('''
               WITH global_rank AS (
                    WITH scores AS (
                        SELECT user_id, COUNT(*) AS score FROM task_run
                        WHERE user_id IS NOT NULL GROUP BY user_id)
                    SELECT user_id, score, rank() OVER (ORDER BY score desc)
                    FROM scores)
               SELECT rank, id, name, fullname, email_addr, info, created,
               score FROM global_rank
               JOIN public."user" on (user_id=public."user".id) ORDER BY rank
               LIMIT :limit;
               ''')

    results = session.execute(sql, dict(limit=n))

    u = User()

    top_users = []
    user_in_top = False
    for row in results:
        if (row.id == user_id):
            user_in_top = True
        user = dict(
            rank=row.rank,
            id=row.id,
            name=row.name,
            fullname=row.fullname,
            email_addr=row.email_addr,
            info=row.info,
            created=row.created,
            score=row.score)
        tmp = u.to_public_json(data=user)
        top_users.append(tmp)
    if (user_id is not None):
        if not user_in_top:
            sql = text('''
                       WITH global_rank AS (
                            WITH scores AS (
                                SELECT user_id, COUNT(*) AS score FROM task_run
                                WHERE user_id IS NOT NULL GROUP BY user_id)
                            SELECT user_id, score, rank() OVER
                                (ORDER BY score desc)
                            FROM scores)
                       SELECT rank, id, name, fullname, email_addr, info, created,
                              score FROM global_rank
                       JOIN public."user" on (user_id=public."user".id)
                       WHERE user_id=:user_id ORDER BY rank;
                       ''')
            user_rank = session.execute(sql, dict(user_id=user_id))
            u = User.query.get(user_id)
            # Load by default user data with no rank
            user = dict(
                rank=-1,
                id=u.id,
                name=u.name,
                fullname=u.fullname,
                email_addr=u.email_addr,
                info=u.info,
                created=u.created,
                score=-1)
            user = u.to_public_json(data=user)
            for row in user_rank:  # pragma: no cover
                user = dict(
                    rank=row.rank,
                    id=row.id,
                    name=row.name,
                    fullname=row.fullname,
                    email_addr=row.email_addr,
                    info=row.info,
                    created=row.created,
                    score=row.score)
                user = u.to_public_json(data=user)
            top_users.append(user)

    return top_users


@memoize(timeout=timeouts.get('USER_TIMEOUT'))
def get_user_summary(name):
    """Return user summary."""
    sql = text('''
               SELECT "user".id, "user".name, "user".fullname, "user".created,
               "user".api_key, "user".twitter_user_id, "user".facebook_user_id,
               "user".google_user_id, "user".info,
               "user".email_addr, COUNT(task_run.user_id) AS n_answers,
               "user".valid_email, "user".confirmation_email_sent
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
                    info=row.info,
                    email_addr=row.email_addr, n_answers=row.n_answers,
                    valid_email=row.valid_email,
                    confirmation_email_sent=row.confirmation_email_sent,
                    registered_ago=pretty_date(row.created))
    if user:
        rank_score = rank_and_score(user['id'])
        user['rank'] = rank_score['rank']
        user['score'] = rank_score['score']
        user['total'] = get_total_users()
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
    # See: https://gist.github.com/tokumine/1583695
    sql = text('''
               WITH global_rank AS (
                    WITH scores AS (
                        SELECT user_id, COUNT(*) AS score FROM task_run
                        WHERE user_id IS NOT NULL GROUP BY user_id)
                    SELECT user_id, score, rank() OVER (ORDER BY score desc)
                    FROM scores)
               SELECT * from global_rank WHERE user_id=:user_id;
               ''')
    results = session.execute(sql, dict(user_id=user_id))
    rank_and_score = dict(rank=None, score=None)
    for row in results:
        rank_and_score['rank'] = row.rank
        rank_and_score['score'] = row.score
    return rank_and_score


def projects_contributed(user_id):
    """Return projects that user_id has contributed to."""
    sql = text('''
               WITH projects_contributed as
                    (SELECT DISTINCT(project_id) FROM task_run
                     WHERE user_id=:user_id)
               SELECT project.id, project.name, project.short_name, project.owner_id,
               project.description, project.info FROM project, projects_contributed
               WHERE project.id=projects_contributed.project_id ORDER BY project.name DESC;
               ''')
    results = session.execute(sql, dict(user_id=user_id))
    projects_contributed = []
    for row in results:
        project = dict(id=row.id, name=row.name, short_name=row.short_name,
                       owner_id=row.owner_id,
                       description=row.description,
                       overall_progress=overall_progress(row.id),
                       n_tasks=n_tasks(row.id),
                       n_volunteers=n_volunteers(row.id),
                       info=row.info)
        projects_contributed.append(project)
    return projects_contributed


@memoize(timeout=timeouts.get('USER_TIMEOUT'))
def projects_contributed_cached(user_id):
    """Return projects contributed too (cached version)."""
    return projects_contributed(user_id)


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
               SELECT project.id, project.name, project.short_name, project.description,
               project.owner_id,
               project.info
               FROM project
               WHERE project.published=true
               AND project.owner_id=:user_id;
               ''')
    projects_published = []
    results = session.execute(sql, dict(user_id=user_id))
    for row in results:
        project = dict(id=row.id, name=row.name, short_name=row.short_name,
                       owner_id=row.owner_id,
                       description=row.description,
                       overall_progress=overall_progress(row.id),
                       n_tasks=n_tasks(row.id),
                       n_volunteers=n_volunteers(row.id),
                       info=row.info)
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
               SELECT project.id, project.name, project.short_name, project.description,
               project.owner_id,
               project.info
               FROM project
               WHERE project.owner_id=:user_id
               AND project.published=false;
               ''')
    projects_draft = []
    results = session.execute(sql, dict(user_id=user_id))
    for row in results:
        project = dict(id=row.id, name=row.name, short_name=row.short_name,
                       owner_id=row.owner_id,
                       description=row.description,
                       overall_progress=overall_progress(row.id),
                       n_tasks=n_tasks(row.id),
                       n_volunteers=n_volunteers(row.id),
                       info=row.info)
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


@cache(timeout=timeouts.get('USER_TOTAL_TIMEOUT'),
         key_prefix="site_total_active_users")
def get_total_active_users():
    """Return total number of users who have submitted atleast one task run"""
    count = session.query(TaskRun.user_id)\
                   .filter(TaskRun.user_id.isnot(None))\
                   .distinct().count()
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


def delete_user_summary(name):
    """Delete from cache the user summary."""
    delete_memoized(get_user_summary, name)
