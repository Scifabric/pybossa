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

from flask import abort


class TaskRunAuth(object):
    _specific_actions = []

    def __init__(self, task_repo, project_repo, result_repo):
        self.task_repo = task_repo
        self.project_repo = project_repo
        self.result_repo = result_repo

    @property
    def specific_actions(self):
        return self._specific_actions

    def admin_subadmin_proj_owners(self, user, taskrun):
        if user.is_anonymous:
            return False
        if user.admin or user.subadmin:
            return True
        project = self.project_repo.get(taskrun.project_id)
        return user.id in project.owners_ids

    def can(self, user, action, taskrun=None):
        action = ''.join(['_', action])
        return getattr(self, action)(user, taskrun)

    def _create(self, user, taskrun):
        project = self.project_repo.get(taskrun.project_id)
        if project is None:
            return False
        if (user.is_anonymous and
                project.allow_anonymous_contributors is False):
            return False
        authorized = self.task_repo.count_task_runs_with(
            project_id=taskrun.project_id,
            task_id=taskrun.task_id,
            user_id=taskrun.user_id,
            user_ip=taskrun.user_ip,
            external_uid=taskrun.external_uid) <= 0

        if not authorized:
            raise abort(403)
        return authorized

    def _read(self, user, taskrun=None):
        if taskrun is not None:
            return self.admin_subadmin_proj_owners(user, taskrun)
        return user.is_authenticated

    def _update(self, user, taskrun):
        return self._delete(user, taskrun)

    def _delete(self, user, taskrun):
        if user.is_anonymous:
            return False
        result = self.result_repo.get_by(project_id=taskrun.project_id,
                                         task_id=taskrun.task_id)
        if result and (taskrun.id in result.task_run_ids):
            return False
        if taskrun.user_id is None:
            return user.admin
        return user.admin or taskrun.user_id == user.id
