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
"""Cache module with helper functions."""

from flask import current_app
from sqlalchemy.sql import text
from pybossa.core import db
from pybossa.cache import memoize, ONE_HOUR
from pybossa.cache.projects import n_results
from pybossa.model.project_stats import ProjectStats


session = db.slave_session


@memoize(timeout=ONE_HOUR * 3)
def n_available_tasks(project_id, user_id=None, user_ip=None):
    """Return the number of tasks for a given project a user can contribute to.

    based on the completion of the project tasks, and previous task_runs
    submitted by the user.
    """
    if user_id and not user_ip:
        query = text('''SELECT COUNT(id) AS n_tasks FROM task WHERE NOT EXISTS
                       (SELECT task_id FROM task_run WHERE
                       project_id=:project_id AND user_id=:user_id
                       AND task_id=task.id)
                       AND project_id=:project_id AND state !='completed';''')
        result = session.execute(query, dict(project_id=project_id,
                                             user_id=user_id))
    else:
        if not user_ip:
            user_ip = '127.0.0.1'
        query = text('''SELECT COUNT(id) AS n_tasks FROM task WHERE NOT EXISTS
                       (SELECT task_id FROM task_run WHERE
                       project_id=:project_id AND user_ip=:user_ip
                       AND task_id=task.id)
                       AND project_id=:project_id AND state !='completed';''')

        result = session.execute(query, dict(project_id=project_id,
                                             user_ip=user_ip))
    n_tasks = 0
    for row in result:
        n_tasks = row.n_tasks
    return n_tasks


def check_contributing_state(project, user_id=None, user_ip=None,
                             external_uid=None, ps=None):
    """Return the state of a given project for a given user.

    Depending on whether the project is completed or not and the user can
    contribute more to it or not.
    """
    project_id = project['id'] if type(project) == dict else project.id
    published = project['published'] if type(project) == dict else project.published
    states = ('completed', 'draft', 'publish', 'can_contribute', 'cannot_contribute')
    if ps is None:
        ps = session.query(ProjectStats)\
                    .filter_by(project_id=project_id).first()
    if ps.overall_progress >= 100:
        return states[0]
    if not published:
        if has_no_presenter(project) or _has_no_tasks(project_id):
            return states[1]
        return states[2]
    if n_available_tasks(project_id, user_id=user_id, user_ip=user_ip) > 0:
        return states[3]
    return states[4]


def add_custom_contrib_button_to(project, user_id_or_ip, ps=None):
    """Add a customized contrib button for a project."""
    if type(project) != dict:
        project = project.dictize()
    project['contrib_button'] = check_contributing_state(project,
                                                         ps=ps,
                                                         **user_id_or_ip)
    if ps is None:
        ps = session.query(ProjectStats)\
                    .filter_by(project_id=project['id']).first()

    project['n_blogposts'] = ps.n_blogposts
    project['n_results'] = ps.n_results

    return project


def has_no_presenter(project):
    """Return if a project has no presenter."""
    if current_app.config.get('DISABLE_TASK_PRESENTER'):
        return False
    else:
        empty_presenters = ('', None)
        try:
            return not project.has_presenter()
        except AttributeError:
            try:
                return (project.get('info').get('task_presenter') in
                        empty_presenters)
            except AttributeError:
                return True


def _has_no_tasks(project_id):
    """Return if a project has no tasks."""
    query = text('''SELECT COUNT(id) AS n_tasks FROM task
               WHERE project_id=:project_id;''')
    result = session.execute(query, dict(project_id=project_id))
    for row in result:
        n_tasks = row.n_tasks
    return n_tasks == 0
