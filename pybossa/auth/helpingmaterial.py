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


class HelpingMaterialAuth(object):
    _specific_actions = []

    def __init__(self, project_repo):
        self.project_repo = project_repo

    @property
    def specific_actions(self):
        return self._specific_actions

    def can(self, user, action, helpingmaterial=None, project_id=None):
        action = ''.join(['_', action])
        return getattr(self, action)(user, helpingmaterial, project_id)

    def _create(self, user, helpingmaterial=None, project_id=None):
        if user.is_anonymous or (helpingmaterial is None and project_id is None):
            return False
        project = self._get_project(helpingmaterial, project_id)
        if helpingmaterial is None:
            return self._is_admin_or_owner(user, project)
        return self._is_admin_or_owner(user, project)

    def _read(self, user, helpingmaterial=None, project_id=None):
        if helpingmaterial or project_id:
            project = self._get_project(helpingmaterial, project_id)
            if project:
                return (project.published or self._is_admin_or_owner(user, project))
            if user.is_anonymous or (helpingmaterial is None and project_id is None):
                return False
            return self._is_admin_or_owner(user, project)
        else:
            return True

    def _update(self, user, helpingmaterial, project_id=None):
        project = self._get_project(helpingmaterial, project_id)
        if user.is_anonymous:
            return False
        return self._is_admin_or_owner(user, project)

    def _delete(self, user, helpingmaterial, project_id=None):
        project = self._get_project(helpingmaterial, project_id)
        if user.is_anonymous:
            return False
        return self._is_admin_or_owner(user, project)

    def _get_project(self, helpingmaterial, project_id):
        if helpingmaterial is not None:
            return self.project_repo.get(helpingmaterial.project_id)
        return self.project_repo.get(project_id)

    def _is_admin_or_owner(self, user, project):
        return (not user.is_anonymous and
                (project.owner_id == user.id or user.admin))
