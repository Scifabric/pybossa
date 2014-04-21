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
"""This module tests the Uploader class."""

from default import Test, with_context
from pybossa.uploader import Uploader
from mock import patch


class TestUploader(Test):

    """Test PyBossa Uploader module."""

    def setUp(self):
        """SetUp method."""
        super(TestUploader, self).setUp()
        with self.flask_app.app_context():
            self.create()

    @with_context
    def test_uploader_init(self):
        """Test UPLOADER init method works."""
        u = Uploader()
        new_extensions = ['pdf', 'doe']
        new_uploader = Uploader()
        with patch.dict(self.flask_app.config,
                        {'ALLOWED_EXTENSIONS': new_extensions}):
            new_uploader.init_app(self.flask_app)
            expected_extensions = set.union(u.allowed_extensions, new_extensions)
            err_msg = "The new uploader should support two extra extensions"
            assert expected_extensions == new_uploader.allowed_extensions, err_msg

    @with_context
    def test_allowed_file(self):
        """Test UPLOADER allowed_file method works."""
        u = Uploader()
        for ext in u.allowed_extensions:
            # Change extension to uppercase to check that it works too
            filename = 'test.%s' % ext.upper()
            err_msg = ("This file: %s should be allowed, but it failed"
                       % filename)
            assert u.allowed_file(filename) is True, err_msg

        err_msg = "Non allowed extensions should return false"
        assert u.allowed_file('wrong.pdf') is False, err_msg
