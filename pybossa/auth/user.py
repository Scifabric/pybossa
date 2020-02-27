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


class UserAuth(object):
    _specific_actions = []

    @property
    def specific_actions(self):
        return self._specific_actions

    def can(self, user, action, resource_user=None):
        action = ''.join(['_', action])
        return getattr(self, action)(user, resource_user)

    def _create(self, user, resource_user=None):
        return user.is_authenticated and user.admin is True

    def _read(self, user, resource_user=None):
        if not user.is_authenticated:
            return False
        if resource_user is None:
            return True
        if user.id == resource_user.id:
            return True
        return user.admin or user.subadmin

    def _update(self, user, resource_user):
        if user.is_anonymous:
            return False
        return self._create(user, resource_user) or resource_user.id == user.id

    def _delete(self, user, resource_user):
        return self._update(user, resource_user)
