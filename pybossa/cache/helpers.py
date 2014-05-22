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

from pybossa.model.app import App
from pybossa.core import timeouts
from pybossa.cache import memoize
from pybossa.cache.apps import overall_progress
from pybossa.sched import new_task



@memoize(timeout=60)
def n_available_tasks(app_id, user_id=None, user_ip=None):
    """Returns the number of tasks for a given app a user can contribute to,
    based on the completion of the app tasks, and previous task_runs submitted
    by the user"""
    tasks = new_task(app_id, user_id=user_id, user_ip=user_ip)
    return tasks


def check_contributing_state(app_id, user_id=None, user_ip=None):
    """Returns the state of a given app for a given user, depending on whether
    the app is completed or not and the user can contribute more to it or not"""

    states = ('completed', 'can_contribute', 'cannot_contribute')
    if overall_progress(app_id) >= 100:
        return states[0]
    if n_available_tasks(app_id, user_id=user_id, user_ip=user_ip) is not None:
        return states[1]
    return states[2]


def add_custom_contrib_button_to(app, user_id_ip):
    app['contrib_button'] = check_contributing_state(app['id'], **user_id_ip)
    return app




