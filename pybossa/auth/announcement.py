# -*- coding: utf8 -*-
# This file is part of PYBOSSA.
#
# Copyright (C) 2017 Scifabric LTD.
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


class AnnouncementAuth(object):
    _specific_actions = []

    def __init__(self, project_repo):
        self.project_repo = project_repo

    @property
    def specific_actions(self):
        return self._specific_actions

    def can(self, user, action, announcement=None):
        action = ''.join(['_', action])
        return getattr(self, action)(user, announcement, project_id)

    def _create(self, user, announcement=None):
        if user.is_anonymous() or (announcement is None and project_id is None):
            return False
        project = self._get_project(announcement)
        if announcement is None:
            return project.owner_id == user.id
        return announcement.user_id == project.owner_id == user.id

    def _read(self, user, announcement=None):
        if announcement or project_id:
            project = self._get_project(announcement, project_id)
            if project:
                return (project.published or self._is_admin_or_owner(user, project))
            if user.is_anonymous() or (announcement is None):
                return False
            return self._is_admin_or_owner(user, project)
        else:
            return True

    def _update(self, user, announcement):
        if user.is_anonymous():
            return False
        return announcement.user_id == user.id

    def _delete(self, user, announcement):
        if user.is_anonymous():
            return False
        return user.admin or announcement.user_id == user.id

    # def _get_project(self, announcement, project_id):
    #     if announcement is not None:
    #         return self.project_repo.get(announcement.project_id)
    #     return self.project_repo.get(project_id)

    def _is_admin_or_owner(self, user):
        return (not user.is_anonymous() and user.admin)
