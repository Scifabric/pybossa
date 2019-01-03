# -*- coding: utf8 -*-
# This file is part of PYBOSSA.
#
# Copyright (C) 2015 SF Isle of Man Limited
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


class WebhookAuth(object):

    _specific_actions = []

    def __init__(self, project_repo):
        self.project_repo = project_repo

    @property
    def specific_actions(self):
        return self._specific_actions

    def can(self, user, action, webhook=None, project_id=None):
        action = ''.join(['_', action])
        return getattr(self, action)(user, webhook, project_id)

    def _create(self, user, webhook, project_id=None):
        return False

    def _read(self, user, webhook=None, project_id=None):
        if user.is_anonymous or (webhook is None and project_id is None):
            return False
        project = self._get_project(webhook, project_id)
        return user.admin or user.id in project.owners_ids

    def _update(self, user, webhook, project_id=None):
        return False

    def _delete(self, user, webhook, project_id=None):
        return False

    def _get_project(self, webhook, project_id):
        if webhook is not None:
            return self.project_repo.get(webhook.project_id)
        return self.project_repo.get(project_id)
