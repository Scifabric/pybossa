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


class ProjectAuth(object):
    _specific_actions = ['publish']

    def __init__(self, task_repo, result_repo):
        self.task_repo = task_repo
        self.result_repo = result_repo

    @property
    def specific_actions(self):
        return self._specific_actions

    def can(self, user, action, taskrun=None):
        action = ''.join(['_', action])
        return getattr(self, action)(user, taskrun)

    def _create(self, user, project=None):
        if project is not None and user.is_authenticated:
            return project.published != True
        return user.is_authenticated

    def _read(self, user, project=None):
        if project is not None and project.published is False:
            return self._only_admin_or_owner(user, project)
        return True

    def _update(self, user, project):
        return self._only_admin_or_owner(user, project)

    def _delete(self, user, project):
        if self.result_repo.get_by(project_id=project.id):
            return False
        return self._only_admin_or_owner(user, project)

    def _publish(self, user, project):
        return (project.has_presenter() and
            len(self.task_repo.filter_tasks_by(project_id=project.id)) > 0 and
            self._only_admin_or_owner(user, project))

    def _only_admin_or_owner(self, user, project):
        return (not user.is_anonymous and
                (user.id in project.owners_ids or user.admin))
