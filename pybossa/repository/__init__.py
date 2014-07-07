# -*- coding: utf8 -*-
# This file is part of PyBossa.
#
# Copyright (C) 2014 SF Isle of Man Limited
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
# Cache global variables for timeouts

""" This package exports the following repository objects as an abstraction
layer between the ORM and the application:

    * user_repo
    * project_repo

The responsibility of these repositories is only fetching one or many objects of
a kind and/or saving them to the DB by calling the ORM apropriate methods.

For more complex DB queries, refer to other packages or services within PyBossa."""

from project_repository import ProjectRepository
from user_repository import UserRepository
