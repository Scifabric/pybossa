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

from flask.ext.login import current_user
import pybossa.model as model
from pybossa.core import db

def create(blogpost=None, app_id=None):
    if current_user.is_anonymous() or (blogpost is None and app_id is None):
        return False
    app = _get_app(blogpost, app_id)
    if blogpost is None:
        return app.owner_id == current_user.id
    return blogpost.user_id == app.owner_id == current_user.id


def read(blogpost=None, app_id=None):
    app = _get_app(blogpost, app_id)
    if app and not app.hidden:
        return True
    if current_user.is_anonymous() or (blogpost is None and app_id is None):
        return False
    return current_user.admin or current_user.id == app.owner_id


def update(blogpost):
    if current_user.is_anonymous():
        return False
    return blogpost.user_id == current_user.id


def delete(blogpost):
    if current_user.is_anonymous():
        return False
    else:
        return current_user.admin or blogpost.user_id == current_user.id


def _get_app(blogpost, app_id):
    if blogpost is not None:
        return db.session.query(model.app.App).get(blogpost.app_id)
    else:
        return db.session.query(model.app.App).get(app_id)




