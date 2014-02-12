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
"""
PyBossa api module for exposing Global Stats via an API.

This package adds GET method for Global Stats.

"""
import json
from api_base import APIBase
from flask import Response
import pybossa.view.stats as stats
import pybossa.cache.apps as cached_apps

class GlobalStatsAPI(APIBase):
    def get(self, id):
        n_pending_tasks = stats.n_total_tasks_site() - stats.n_task_runs_site()
        n_users = stats.n_auth_users() + stats.n_anon_users()
        n_projects = cached_apps.n_published() + cached_apps.n_draft()
        data = dict(n_projects=n_projects,
                    n_users=n_users,
                    n_task_runs=stats.n_task_runs_site(),
                    n_pending_tasks=n_pending_tasks)
        return Response(json.dumps(data), 200, mimetype='application/json')

    def _post(self):
        raise MethodNotAllowed
