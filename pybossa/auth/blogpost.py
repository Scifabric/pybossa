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

def create(blogpost):
    if current_user.is_anonymous():
        return False
    if blogpost.app is None:
        app = db.session.query(model.app.App).filter_by(id=blogpost.app_id).first()
        blogpost.app = app
    return blogpost.user_id == blogpost.app.owner_id == current_user.id


def read(blogpost=None):
    return True


def update(blogpost):
    if current_user.is_anonymous():
        return False
    return blogpost.user_id == current_user.id


def delete(blogpost):
    if current_user.is_anonymous():
        return False
    else:
        return current_user.admin or blogpost.user_id == current_user.id