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


class ProjectStatsAuth(object):

    _specific_actions = []

    def __init__(self):
        pass

    @property
    def specific_actions(self):
        return self._specific_actions

    def can(self, user, action, webhook=None, project_id=None):
        action = ''.join(['_', action])
        return getattr(self, action)(user, webhook, project_id)

    def _create(self, user, webhook, project_id=None):
        return False

    def _read(self, user, webhook=None, project_id=None):
        return True

    def _update(self, user, webhook, project_id=None):
        return False

    def _delete(self, user, webhook, project_id=None):
        return False
