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

import inspect
from flask import abort
from flask.ext.login import current_user

import app
import task
import taskrun
import rundata
import category
import user

class Requirement(object):
    """ Checks a function call and raises an exception if the
    function returns a non-True value. """

    def __init__(self, wrapped):
        self.wrapped = wrapped

    def __getattr__(self, attr):
        real = getattr(self.wrapped, attr)
        return Requirement(real)

    def __call__(self, *args, **kwargs):
        fc = self.wrapped(*args, **kwargs)
        if fc is not True:
            if current_user.is_anonymous():
                raise abort(403)
            else:
                raise abort(401)
        return fc

    @classmethod
    def here(cls):
        module = inspect.getmodule(cls)
        return cls(module)

require = Requirement.here()
