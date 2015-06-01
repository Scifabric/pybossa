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
"""Cache module for projects."""
from sqlalchemy.sql import text
from pybossa.core import db, timeouts
from pybossa.model.project import Project
from pybossa.util import pretty_date
from pybossa.cache import memoize, cache, delete_memoized, delete_cached

import json


session = db.slave_session


@memoize(timeout=timeouts.get('APP_TIMEOUT'))
def get_project(short_name):
    """Get project by short_name."""
    project = session.query(Project).filter_by(short_name=short_name).first()
    return project


@cache(timeout=timeouts.get('STATS_FRONTPAGE_TIMEOUT'),
       key_prefix="front_page_top_projects")
def get_top(n=4):
    """Return top n=4 projects."""
    sql = text('''SELECT project.id, project.name, project.short_name, project.description,
               project.info,
               COUNT(project_id) AS total FROM task_run, project
               WHERE project_id IS NOT NULL AND project.id=project_id AND project.hidden=0
               GROUP BY project.id ORDER BY total DESC LIMIT :limit;''')
    results = session.execute(sql, dict(limit=n))
    top_projects = []
    for row in results:
        project = dict(id=row.id, name=row.name, short_name=row.short_name,
                       description=row.description,
                       info=json.loads(row.info),
                       n_volunteers=n_volunteers(row.id),
                       n_completed_tasks=n_completed_tasks(row.id))
        top_projects.append(project)
    return top_projects


@memoize(timeout=timeouts.get('BROWSE_TASKS_TIMEOUT'))
def browse_tasks(project_id):
    """Cache browse tasks view for a project."""
    sql = text('''
               SELECT task.id, count(task_run.id) as n_task_runs, task.n_answers
               FROM task LEFT OUTER JOIN task_run ON (task.id=task_run.task_id)
               WHERE task.project_id=:project_id
               GROUP BY task.id ORDER BY task.id''')
    results = session.execute(sql, dict(project_id=project_id))
    tasks = []
    for row in results:
        task = dict(id=row.id, n_task_runs=row.n_task_runs,
                    n_answers=row.n_answers)
        task['pct_status'] = _pct_status(row.n_task_runs, row.n_answers)
        tasks.append(task)
    return tasks


def _pct_status(n_task_runs, n_answers):
    """Return percentage status."""
    if n_answers != 0 and n_answers is not None:
        # Check if it's bigger the n_task_runs that n_answers
        if n_task_runs > n_answers:
            return float(1)
        else:
            return float(n_task_runs) / n_answers
    return float(0)


@memoize(timeout=timeouts.get('APP_TIMEOUT'))
def n_tasks(project_id):
    """Return number of tasks of a project."""
    sql = text('''SELECT COUNT(task.id) AS n_tasks FROM task
                  WHERE task.project_id=:project_id''')
    results = session.execute(sql, dict(project_id=project_id))
    n_tasks = 0
    for row in results:
        n_tasks = row.n_tasks
    return n_tasks


@memoize(timeout=timeouts.get('APP_TIMEOUT'))
def n_completed_tasks(project_id):
    """Return number of completed tasks of a project."""
    sql = text('''SELECT COUNT(task.id) AS n_completed_tasks FROM task
                WHERE task.project_id=:project_id AND task.state=\'completed\';''')

    results = session.execute(sql, dict(project_id=project_id))
    n_completed_tasks = 0
    for row in results:
        n_completed_tasks = row.n_completed_tasks
    return n_completed_tasks


@memoize(timeout=timeouts.get('REGISTERED_USERS_TIMEOUT'))
def n_registered_volunteers(project_id):
    """Return number of registered users that have participated in a project."""
    sql = text('''SELECT COUNT(DISTINCT(task_run.user_id))
               AS n_registered_volunteers FROM task_run
               WHERE task_run.user_id IS NOT NULL AND
               task_run.user_ip IS NULL AND
               task_run.project_id=:project_id;''')

    results = session.execute(sql, dict(project_id=project_id))
    n_registered_volunteers = 0
    for row in results:
        n_registered_volunteers = row.n_registered_volunteers
    return n_registered_volunteers


@memoize(timeout=timeouts.get('ANON_USERS_TIMEOUT'))
def n_anonymous_volunteers(project_id):
    """Return number of anonymous users that have participated in a project."""
    sql = text('''SELECT COUNT(DISTINCT(task_run.user_ip))
               AS n_anonymous_volunteers FROM task_run
               WHERE task_run.user_ip IS NOT NULL AND
               task_run.user_id IS NULL AND
               task_run.project_id=:project_id;''')

    results = session.execute(sql, dict(project_id=project_id))
    n_anonymous_volunteers = 0
    for row in results:
        n_anonymous_volunteers = row.n_anonymous_volunteers
    return n_anonymous_volunteers


def n_volunteers(project_id):
    """Return total number of volunteers of a project."""
    total = (n_anonymous_volunteers(project_id) +
             n_registered_volunteers(project_id))
    return total


@memoize(timeout=timeouts.get('APP_TIMEOUT'))
def n_task_runs(project_id):
    """Return number of task_runs of a project."""
    sql = text('''SELECT COUNT(task_run.id) AS n_task_runs FROM task_run
                  WHERE task_run.project_id=:project_id''')

    results = session.execute(sql, dict(project_id=project_id))
    n_task_runs = 0
    for row in results:
        n_task_runs = row.n_task_runs
    return n_task_runs


@memoize(timeout=timeouts.get('APP_TIMEOUT'))
def overall_progress(project_id):
    """Return the percentage of completed tasks for a project."""
    if n_tasks(project_id) != 0:
        return ((n_completed_tasks(project_id) * 100) / n_tasks(project_id))
    else:
        return 0


@memoize(timeout=timeouts.get('APP_TIMEOUT'))
def last_activity(project_id):
    """Return last activity, date, from a project."""
    sql = text('''SELECT finish_time FROM task_run WHERE project_id=:project_id
               ORDER BY finish_time DESC LIMIT 1''')

    results = session.execute(sql, dict(project_id=project_id))
    for row in results:
        if row is not None:
            return row[0]
        else:  # pragma: no cover
            return None


# This function does not change too much, so cache it for a longer time
@cache(timeout=timeouts.get('STATS_FRONTPAGE_TIMEOUT'),
       key_prefix="number_featured_projects")
def _n_featured():
    """Return number of featured projects."""
    sql = text('''SELECT COUNT(*) FROM project WHERE featured=true;''')

    results = session.execute(sql)
    for row in results:
        count = row[0]
    return count


# This function does not change too much, so cache it for a longer time
@memoize(timeout=timeouts.get('STATS_FRONTPAGE_TIMEOUT'))
def get_all_featured(category=None):
    """Return a list of featured projects with a pagination."""
    sql = text('''SELECT project.id, project.name, project.short_name, project.info,
               project.created, project.updated, project.description,
               "user".fullname AS owner FROM project, "user"
               WHERE project.featured=true AND project.hidden=0
               AND "user".id=project.owner_id GROUP BY project.id, "user".id;''')

    results = session.execute(sql)
    projects = []
    for row in results:
        project = dict(id=row.id, name=row.name, short_name=row.short_name,
                       created=row.created, description=row.description,
                       updated=row.updated,
                       last_activity=pretty_date(last_activity(row.id)),
                       last_activity_raw=last_activity(row.id),
                       owner=row.owner,
                       overall_progress=overall_progress(row.id),
                       n_tasks=n_tasks(row.id),
                       n_volunteers=n_volunteers(row.id),
                       info=dict(json.loads(row.info)))
        projects.append(project)
    return projects


def get_featured(category=None, page=1, per_page=5):
    """Return a list of featured project with a pagination."""
    offset = (page - 1) * per_page
    return get_all_featured()[offset:offset+per_page]


@cache(key_prefix="number_published_projects",
       timeout=timeouts.get('STATS_APP_TIMEOUT'))
def n_published():
    """Return number of published projects."""
    sql = text('''
               WITH published_projects as
               (SELECT project.id FROM project, task WHERE
               project.id=task.project_id AND project.hidden=0 AND project.info
               LIKE('%task_presenter%') GROUP BY project.id)
               SELECT COUNT(id) FROM published_projects;
               ''')

    results = session.execute(sql)
    for row in results:
        count = row[0]
    return count


# Cache it for longer times, as this is only shown to admin users
@cache(timeout=timeouts.get('STATS_DRAFT_TIMEOUT'),
       key_prefix="number_draft_projects")
def _n_draft():
    """Return number of draft projects."""
    sql = text('''SELECT COUNT(project.id) FROM project
               LEFT JOIN task on project.id=task.project_id
               WHERE task.project_id IS NULL
               AND project.info NOT LIKE('%task_presenter%')
               AND project.hidden=0;''')

    results = session.execute(sql)
    for row in results:
        count = row[0]
    return count


@memoize(timeout=timeouts.get('STATS_FRONTPAGE_TIMEOUT'))
def get_all_draft(category=None):
    """Return list of all draft projects."""
    sql = text('''SELECT project.id, project.name, project.short_name, project.created,
               project.description, project.info, project.updated, "user".fullname as owner
               FROM "user", project LEFT JOIN task ON project.id=task.project_id
               WHERE task.project_id IS NULL
               AND project.info NOT LIKE('%task_presenter%')
               AND project.hidden=0
               AND project.owner_id="user".id;''')

    results = session.execute(sql)
    projects = []
    for row in results:
        project = dict(id=row.id, name=row.name, short_name=row.short_name,
                       created=row.created,
                       updated=row.updated,
                       description=row.description,
                       owner=row.owner,
                       last_activity=pretty_date(last_activity(row.id)),
                       last_activity_raw=last_activity(row.id),
                       overall_progress=overall_progress(row.id),
                       n_tasks=n_tasks(row.id),
                       n_volunteers=n_volunteers(row.id),
                       info=dict(json.loads(row.info)))
        projects.append(project)
    return projects

def get_draft(category=None, page=1, per_page=5):
    """Return a list of draft project with a pagination."""
    offset = (page - 1) * per_page
    return get_all_draft()[offset:offset+per_page]


@memoize(timeout=timeouts.get('N_APPS_PER_CATEGORY_TIMEOUT'))
def n_count(category):
    """Count the number of projects in a given category."""
    if category == 'featured':
        return _n_featured()
    if category == 'draft':
        return _n_draft()
    sql = text('''
               WITH uniq AS (
               SELECT COUNT(project.id) FROM task, project
               LEFT OUTER JOIN category ON project.category_id=category.id
               WHERE
               category.short_name=:category
               AND project.hidden=0
               AND project.info LIKE('%task_presenter%')
               AND task.project_id=project.id
               GROUP BY project.id)
               SELECT COUNT(*) FROM uniq
               ''')

    results = session.execute(sql, dict(category=category))
    count = 0
    for row in results:
        count = row[0]
    return count


@memoize(timeout=timeouts.get('APP_TIMEOUT'))
def get_all(category):
    """Return a list of projects with at least one task and a task_presenter.
    """
    sql = text('''SELECT project.id, project.name, project.short_name,
               project.description, project.info, project.created, project.updated,
               project.category_id, project.featured, "user".fullname AS owner
               FROM "user", task, project
               LEFT OUTER JOIN category ON project.category_id=category.id
               WHERE
               category.short_name=:category
               AND project.hidden=0
               AND "user".id=project.owner_id
               AND project.info LIKE('%task_presenter%')
               AND task.project_id=project.id
               GROUP BY project.id, "user".id ORDER BY project.name;''')

    results = session.execute(sql, dict(category=category))
    projects = []
    for row in results:
        project = dict(id=row.id,
                       name=row.name, short_name=row.short_name,
                       created=row.created,
                       updated=row.updated,
                       description=row.description,
                       owner=row.owner,
                       featured=row.featured,
                       last_activity=pretty_date(last_activity(row.id)),
                       last_activity_raw=last_activity(row.id),
                       overall_progress=overall_progress(row.id),
                       n_tasks=n_tasks(row.id),
                       n_volunteers=n_volunteers(row.id),
                       info=dict(json.loads(row.info)))
        projects.append(project)
    return projects


def get(category, page=1, per_page=5):
    """Return a list of projects with at least one task and a task_presenter.
    It also returns  a pagination for a given category.
    """
    offset = (page - 1) * per_page
    return get_all(category)[offset:offset+per_page]


# TODO: find a convenient cache timeout and cache, if needed
def get_from_pro_user():
    """Return the list of projects belonging to 'pro' users."""
    sql = text('''SELECT project.id, project.short_name FROM project, "user"
               WHERE project.owner_id="user".id AND "user".pro=True;''')
    results = db.slave_session.execute(sql)
    projects = []
    for row in results:
        project = dict(id=row.id, short_name=row.short_name)
        projects.append(project)
    return projects


def reset():
    """Clean the cache"""
    delete_cached("index_front_page")
    delete_cached('front_page_featured_projects')
    delete_cached('front_page_top_projects')
    delete_cached('number_featured_projects')
    delete_cached('number_published_projects')
    delete_cached('number_draft_projects')
    delete_memoized(get_all_featured)
    delete_memoized(get_all_draft)
    delete_memoized(n_count)
    delete_memoized(get_all)


def delete_project(short_name):
    """Reset project values in cache"""
    delete_memoized(get_project, short_name)


def delete_browse_tasks(project_id):
    """Reset browse_tasks value in cache"""
    delete_memoized(browse_tasks, project_id)


def delete_n_tasks(project_id):
    """Reset n_tasks value in cache"""
    delete_memoized(n_tasks, project_id)


def delete_n_completed_tasks(project_id):
    """Reset n_completed_tasks value in cache"""
    delete_memoized(n_completed_tasks, project_id)


def delete_n_task_runs(project_id):
    """Reset n_tasks value in cache"""
    delete_memoized(n_task_runs, project_id)


def delete_overall_progress(project_id):
    """Reset overall_progress value in cache"""
    delete_memoized(overall_progress, project_id)


def delete_last_activity(project_id):
    """Reset last_activity value in cache"""
    delete_memoized(last_activity, project_id)


def delete_n_registered_volunteers(project_id):
    """Reset n_registered_volunteers value in cache"""
    delete_memoized(n_registered_volunteers, project_id)


def delete_n_anonymous_volunteers(project_id):
    """Reset n_anonymous_volunteers value in cache"""
    delete_memoized(n_anonymous_volunteers, project_id)


def delete_n_volunteers(project_id):
    """Reset n_volunteers value in cache"""
    delete_memoized(n_volunteers, project_id)


def clean(project_id):
    """Clean all items in cache"""
    reset()
    clean_project(project_id)


def clean_project(project_id):
    """Clean cache for a specific project"""
    delete_browse_tasks(project_id)
    delete_n_tasks(project_id)
    delete_n_completed_tasks(project_id)
    delete_n_registered_volunteers(project_id)
    delete_n_anonymous_volunteers(project_id)
    delete_n_volunteers(project_id)
    delete_last_activity(project_id)
    delete_n_task_runs(project_id)
    delete_overall_progress(project_id)
