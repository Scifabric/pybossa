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


class CategoryAuth(object):
    _specific_actions = []

    @property
    def specific_actions(self):
        return self._specific_actions

    def can(self, user, action, category=None):
        action = ''.join(['_', action])
        return getattr(self, action)(user, category)

    def _create(self, user, category=None):
        return self._only_admin(user)

    def _read(self, user, category=None):
        return True

    def _update(self, user, category):
        return self._only_admin(user)

    def _delete(self, user, category):
        return self._only_admin(user)

    def _only_admin(self, user):
        return user.is_authenticated and user.admin
