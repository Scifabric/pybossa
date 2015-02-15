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

    def can(self, user, action, auditlog=None, app_id=None):
        action = ''.join(['_', action])
        return getattr(self, action)(user, auditlog, app_id)

    def _create(self, user, auditlog, app_id=None):
        return False

    def _read(self, user, auditlog=None, app_id=None):
        if user.is_anonymous() or (auditlog is None and app_id is None):
            return False
        app = self._get_app(auditlog, app_id)
        return user.admin or (user.id == app.owner_id and user.pro)

    def _update(self, user, auditlog, app_id=None):
        return False

    def _delete(self, user, auditlog, app_id=None):
        return False

    def _get_app(self, auditlog, app_id):
        if auditlog is not None:
            return self.project_repo.get(auditlog.app_id)
        return self.project_repo.get(app_id)
