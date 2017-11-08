# -*- coding: utf8 -*-
# This file is part of PYBOSSA.
#
# Copyright (C) 2017 Scifabric LTD.
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

from mock import patch, Mock
from pybossa.syncer import Syncer
from default import Test, with_context


class TestSyncer(Test):

    TARGET = {'x': 'I am a target', 'id': 1}
    TARGET_URL = 'http://test.com'
    TARGET_ID = 'some_target_id'

    def setUp(self):
        super(TestSyncer, self).setUp()
        self.syncer = Syncer(self.TARGET_URL)

    @with_context
    def test_cache_target(self):
        self.syncer.cache_target(self.TARGET, self.TARGET_ID)
        cache = self.syncer.get_target_cache(self.TARGET_ID)
        assert cache == self.TARGET

        self.syncer.delete_target_cache(self.TARGET_ID)
        cache = self.syncer.get_target_cache(self.TARGET_ID)
        assert cache == None
