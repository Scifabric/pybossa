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


class AuditlogAuth(object):

    def __init__(self, project_repo):
        self.project_repo = project_repo

    def can(self, user, action, auditlog=None, project_id=None):
        action = ''.join(['_', action])
        return getattr(self, action)(user, auditlog, project_id)

    def _create(self, user, auditlog, project_id=None):
        return False

    def _read(self, user, auditlog=None, project_id=None):
        if user.is_anonymous() or (auditlog is None and project_id is None):
            return False
        project = self._get_project(auditlog, project_id)
        return user.admin or (user.id == project.owner_id and user.pro)

    def _update(self, user, auditlog, project_id=None):
        return False

    def _delete(self, user, auditlog, project_id=None):
        return False

    def _get_project(self, auditlog, project_id):
        if auditlog is not None:
            return self.project_repo.get(auditlog.project_id)
        return self.project_repo.get(project_id)
