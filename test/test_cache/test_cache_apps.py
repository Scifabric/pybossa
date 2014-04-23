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

import hashlib
from default import Test, db, with_context


class TestAppsCache(Test):


    @with_context
    def test_test_n_completed_tasks(self):
        """Test CACHE APPS number of completed apps for a given app"""


    @with_context
    def test_n_registered_volunteers(self):
        """Test CACHE APPS number of registered users contributed to a given app"""


    @with_context
    def test_n_anonymous_volunteers(self):
        """Test CACHE APPS number of anonymous users contributed to a given app"""


    @with_context
    def test_n_volunteers(self):
        """Test CACHE APPS total number of users contributed to a given app"""
