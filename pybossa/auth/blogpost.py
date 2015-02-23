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


class BlogpostAuth(object):

    def __init__(self, project_repo):
        self.project_repo = project_repo

    def can(self, user, action, blogpost=None, app_id=None):
        action = ''.join(['_', action])
        return getattr(self, action)(user, blogpost, app_id)

    def _create(self, user, blogpost=None, app_id=None):
        if user.is_anonymous() or (blogpost is None and app_id is None):
            return False
        app = self._get_app(blogpost, app_id)
        if blogpost is None:
            return app.owner_id == user.id
        return blogpost.user_id == app.owner_id == user.id

    def _read(self, user, blogpost=None, app_id=None):
        app = self._get_app(blogpost, app_id)
        if app and not app.hidden:
            return True
        if user.is_anonymous() or (blogpost is None and app_id is None):
            return False
        return user.admin or user.id == app.owner_id

    def _update(self, user, blogpost, app_id=None):
        if user.is_anonymous():
            return False
        return blogpost.user_id == user.id

    def _delete(self, user, blogpost, app_id=None):
        if user.is_anonymous():
            return False
        return user.admin or blogpost.user_id == user.id

    def _get_app(self, blogpost, app_id):
        if blogpost is not None:
            return self.project_repo.get(blogpost.app_id)
        return self.project_repo.get(app_id)
