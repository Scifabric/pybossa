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

import json
from mock import patch
from base import web, model, Fixtures, db, redis_flushall
import pybossa.vmcp as vmcp
from nose.tools import assert_equal, assert_raises


class TestAPI:

    def test_myquote(self):
        """Test myquote works."""
        # Valid char should be the same
        err_msg = "Valid chars should not be quoted"
        assert vmcp.myquote('a') == 'a', err_msg
        # Non-valid
        err_msg = "Non-Valid chars should be quoted"
        assert vmcp.myquote('%') == '%25', err_msg
