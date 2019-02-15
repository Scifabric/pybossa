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
"""Stats view on PYBOSSA."""
import json
from flask import Blueprint

from pybossa.cache import site_stats
from pybossa.cache import projects as cached_projects
from pybossa.util import handle_content_type
from flask_login import login_required

blueprint = Blueprint('stats', __name__)


@blueprint.route('/')
@login_required
def index():
    """Return Global Statistics for the site."""
    title = "Global Statistics"

    n_auth = site_stats.n_auth_users()

    n_anon = site_stats.n_anon_users()

    n_total_users = n_anon + n_auth

    n_published_projects = cached_projects.n_published()
    n_draft_projects = cached_projects.n_count('draft')
    n_total_projects = n_published_projects + n_draft_projects

    n_tasks = site_stats.n_tasks_site()

    n_task_runs = site_stats.n_task_runs_site()

    top5_projects_24_hours = site_stats.get_top5_projects_24_hours()

    top5_users_24_hours = site_stats.get_top5_users_24_hours()

    stats = dict(n_total_users=n_total_users, n_auth=n_auth, n_anon=n_anon,
                 n_published_projects=n_published_projects,
                 n_draft_projects=n_draft_projects,
                 n_total_projects=n_total_projects,
                 n_tasks=n_tasks,
                 n_task_runs=n_task_runs)

    users = dict(label="User Statistics",
                 values=[
                     dict(label='Anonymous', value=[0, n_anon]),
                     dict(label='Authenticated', value=[0, n_auth])])

    projects = dict(label="Projects Statistics",
                    values=[
                        dict(label='Published',
                             value=[0, n_published_projects]),
                        dict(label='Draft', value=[0, n_draft_projects])])

    tasks = dict(label="Task and Task Run Statistics",
                 values=[
                     dict(label='Tasks', value=[0, n_tasks]),
                     dict(label='Answers', value=[1, n_task_runs])])

    response = dict(template='/stats/global.html', title=title,
                    users=json.dumps(users),
                    projects=json.dumps(projects),
                    tasks=json.dumps(tasks),
                    show_locs=False,
                    top5_users_24_hours=top5_users_24_hours,
                    top5_projects_24_hours=top5_projects_24_hours,
                    stats=stats)
    return handle_content_type(response)
