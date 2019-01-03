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
"""
PYBOSSA api module for exposing Global Stats via an API.

This package adds GET method for Global Stats.

"""
import json
from .api_base import APIBase
from flask import Response
import pybossa.cache.site_stats as stats
import pybossa.cache.projects as cached_projects
import pybossa.cache.categories as cached_categories
from pybossa.util import jsonpify
from pybossa.ratelimit import ratelimit
from werkzeug.exceptions import MethodNotAllowed


class GlobalStatsAPI(APIBase):

    """
    Class for Global Stats of PYBOSSA server.

    Returns global stats as a JSON object.

    """

    @jsonpify
    @ratelimit(limit=300, per=15 * 60)
    def get(self, oid=None):
        """Return global stats."""
        n_pending_tasks = stats.n_total_tasks_site() - stats.n_task_runs_site()
        n_users = stats.n_auth_users() + stats.n_anon_users()
        n_projects = cached_projects.n_published() + cached_projects.n_count('draft')
        data = dict(n_projects=n_projects,
                    n_users=n_users,
                    n_tasks=stats.n_total_tasks_site(),
                    n_task_runs=stats.n_task_runs_site(),
                    n_pending_tasks=n_pending_tasks,
                    n_results=stats.n_results_site(),
                    categories=[])
        # Add Categories
        categories = cached_categories.get_used()
        for c in categories:
            datum = dict()
            datum[c['short_name']] = cached_projects.n_count(c['short_name'])
            data['categories'].append(datum)
        # Add Featured
        datum = dict()
        datum['featured'] = cached_projects.n_count('featured')
        data['categories'].append(datum)
        # Add Draft
        datum = dict()
        datum['draft'] = cached_projects.n_count('draft')
        data['categories'].append(datum)
        return Response(json.dumps(data), 200, mimetype='application/json')

    def post(self):
        raise MethodNotAllowed
