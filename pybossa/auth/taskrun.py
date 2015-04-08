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

from flask import abort


class TaskRunAuth(object):

    def __init__(self, task_repo, project_repo):
        self.task_repo = task_repo
        self.project_repo = project_repo

    def can(self, user, action, taskrun=None):
        action = ''.join(['_', action])
        return getattr(self, action)(user, taskrun)

    def _create(self, user, taskrun):
        project_id = self.task_repo.get_task(taskrun.task_id).project_id
        project = self.project_repo.get(project_id)
        if (user.is_anonymous() and
                project.allow_anonymous_contributors is False):
            return False
        authorized = self.task_repo.count_task_runs_with(
            project_id=taskrun.project_id,
            task_id=taskrun.task_id,
            user_id=taskrun.user_id,
            user_ip=taskrun.user_ip) <= 0
        if not authorized:
            raise abort(403)
        return authorized

    def _read(self, user, taskrun=None):
        return True

    def _update(self, user, taskrun):
        return False

    def _delete(self, user, taskrun):
        if user.is_anonymous():
            return False
        if taskrun.user_id is None:
            return user.admin
        return user.admin or taskrun.user_id == user.id
