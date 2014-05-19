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



@memoize(timeout=60)
def n_available_tasks(app_id, user_id=None, user_ip=None):
    """Returns the number of tasks for a given app a user can contribute to,
    based on the completion of the app tasks, and previous task_runs submitted
    by the user"""

    app = App.query.get(app_id)
    n_tasks = 0
    for task in app.tasks:
        user_answered = user_id in [tr.user_id for tr in task.task_runs]
        anon_answered = user_ip in [tr.user_ip for tr in task.task_runs]
        if task.state != 'completed' and not user_answered and not anon_answered:
            n_tasks += 1
    return n_tasks

