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

import json
from flask import Blueprint
from flask import render_template

from pybossa.cache import site_stats
from pybossa.cache import apps as cached_apps

blueprint = Blueprint('stats', __name__)


@blueprint.route('/')
def index():
    """Return Global Statistics for the site"""

    title = "Global Statistics"

    n_auth = site_stats.n_auth_users()

    n_anon = site_stats.n_anon_users()

    n_total_users = n_anon + n_auth

    n_published_apps = cached_apps.n_published()
    n_draft_apps = cached_apps.n_count('draft')
    n_total_apps = n_published_apps + n_draft_apps

    n_tasks = site_stats.n_tasks_site()

    n_task_runs = site_stats.n_task_runs_site()

    top5_apps_24_hours = site_stats.get_top5_apps_24_hours()

    top5_users_24_hours = site_stats.get_top5_users_24_hours()

    locs = site_stats.get_locs()

    show_locs = False
    if len(locs) > 0:
        show_locs = True

    stats = dict(n_total_users=n_total_users, n_auth=n_auth, n_anon=n_anon,
                 n_published_apps=n_published_apps,
                 n_draft_apps=n_draft_apps,
                 n_total_apps=n_total_apps,
                 n_tasks=n_tasks,
                 n_task_runs=n_task_runs)

    users = dict(label="User Statistics",
                 values=[
                     dict(label='Anonymous', value=[0, n_anon]),
                     dict(label='Authenticated', value=[0, n_auth])])

    apps = dict(label="Apps Statistics",
                values=[
                    dict(label='Published', value=[0, n_published_apps]),
                    dict(label='Draft', value=[0, n_draft_apps])])

    tasks = dict(label="Task and Task Run Statistics",
                 values=[
                     dict(label='Tasks', value=[0, n_tasks]),
                     dict(label='Answers', value=[1, n_task_runs])])

    return render_template('/stats/global.html', title=title,
                           users=json.dumps(users),
                           apps=json.dumps(apps),
                           tasks=json.dumps(tasks),
                           locs=json.dumps(locs),
                           show_locs=show_locs,
                           top5_users_24_hours=top5_users_24_hours,
                           top5_apps_24_hours=top5_apps_24_hours,
                           stats=stats)
