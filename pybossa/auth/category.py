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

class CategoryAuth(object):

    def can(self, user, action, category=None):
        action = ''.join(['_', action])
        return getattr(self, action)(user, category)

    def _create(self, user, category=None):
        if user.is_authenticated():
            if user.admin is True:
                return True
            else:
                return False
        else:
            return False

    def _read(self, user, category=None):
        return True

    def _update(self, user, category):
        return self._create(user, category)

    def _delete(self, user, category):
        return self._create(user, category)
