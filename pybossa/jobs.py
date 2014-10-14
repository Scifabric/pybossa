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

import os

def get_all_jobs():
    return [warm_up_stats]

def warm_up_stats():
    print "Running on the background warm_up_stats"
    from pybossa.cache.site_stats import (n_auth_users, n_anon_users,
        n_tasks_site, n_total_tasks_site, n_task_runs_site,
        get_top5_apps_24_hours, get_top5_users_24_hours, get_locs)

    env_cache_disabled = os.environ.get('PYBOSSA_REDIS_CACHE_DISABLED')
    if not env_cache_disabled:
        os.environ['PYBOSSA_REDIS_CACHE_DISABLED'] = '1'

    n_auth_users()
    n_anon_users()
    n_tasks_site()
    n_total_tasks_site()
    n_task_runs_site()
    get_top5_apps_24_hours()
    get_top5_users_24_hours()
    get_locs()

    if env_cache_disabled is None:
        del os.environ['PYBOSSA_REDIS_CACHE_DISABLED']
    else:
        os.environ['PYBOSSA_REDIS_CACHE_DISABLED'] = env_cache_disabled

    return True