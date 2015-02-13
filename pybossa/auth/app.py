# -*- coding: utf8 -*-
# This file is part of PyBossa.
#
# Copyright (C) 2013 SF Isle of Man Limited
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

class AppAuth(object):

    def can(self, user, action, taskrun=None):
        action = ''.join(['_', action])
        return getattr(self, action)(user, taskrun)

    def _create(self, user, app=None):
        return user.is_authenticated()


    def _read(self, user, app=None):
        if app is None:
            return True
        if app.hidden:
            return self._only_admin_or_owner(user, app)
        return True


    def _update(self, user, app):
        return self._only_admin_or_owner(user, app)


    def _delete(self, user, app):
        return self._only_admin_or_owner(user, app)


    def _only_admin_or_owner(self, user, app):
        return (not user.is_anonymous() and
                    (app.owner_id == user.id or user.admin))
