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


class ResultAuth(object):
    _specific_actions = []

    def __init__(self, project_repo):
        self.project_repo = project_repo

    @property
    def specific_actions(self):
        return self._specific_actions

    def admin_subadmin_proj_owners(self, user, result=None):
        if user.is_anonymous:
            return False
        if user.admin or user.subadmin:
            return True
        if result is None:
            return False
        project = self.project_repo.get(result.project_id)
        return user.id in project.owners_ids

    def can(self, user, action, result=None):
        action = ''.join(['_', action])
        return getattr(self, action)(user, result)

    def _create(self, user, result):
        return not user.is_anonymous and user.admin

    def _read(self, user, result=None):
        return self.admin_subadmin_proj_owners(user, result)

    def _update(self, user, result):
        if user.is_anonymous:
            return False
        project = self._get_project(result, result.project_id)
        return user.admin or (user.subadmin and user.id in project.owners_ids)

    def _delete(self, user, result):
        return False

    def _get_project(self, result, project_id):
        if result is not None:
            return self.project_repo.get(result.project_id)
        return self.project_repo.get(project_id)
