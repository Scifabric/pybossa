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

from base import web, model, Fixtures, db, redis_flushall
from pybossa.uploader import Uploader
from pybossa.uploader.local import LocalUploader
from mock import patch
from werkzeug.datastructures import FileStorage


class TestUploader:

    """Test PyBossa Uploader module."""

    def setUp(self):
        """SetUp method."""
        self.app = web.app.test_client()
        model.rebuild_db()
        redis_flushall()
        Fixtures.create()

    def tearDown(self):
        """Tear Down method."""
        db.session.remove()
        redis_flushall()

    @classmethod
    def teardown_class(cls):
        """Tear Down class."""
        model.rebuild_db()
        redis_flushall()

    def test_uploader_init(self):
        """Test UPLOADER init method works."""
        u = Uploader()
        new_extensions = set(['pdf', 'doe'])
        new_uploader = Uploader(new_extensions)
        expected_extensions = set.union(u.allowed_extensions, new_extensions)
        err_msg = "The new uploader should support two extra extensions"
        assert expected_extensions == new_uploader.allowed_extensions, err_msg

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

    def test_local_uploader_init(self):
        """Test LOCAL UPLOADER init works."""
        u = LocalUploader()
        new_extensions = set(['pdf', 'doe'])
        new_uploader = LocalUploader(upload_folder='/tmp/',
                                     allowed_extensions=new_extensions)
        expected_extensions = set.union(u.allowed_extensions, new_extensions)
        err_msg = "The new uploader should support two extra extensions"
        assert expected_extensions == new_uploader.allowed_extensions, err_msg
        err_msg = "Upload folder by default is /tmp/"
        assert new_uploader.upload_folder == '/tmp/', err_msg

    @patch('werkzeug.datastructures.FileStorage.save', return_value=None)
    def test_local_uploader_upload_correct_file(self, mock):
        """Test LOCAL UPLOADER upload works."""
        mock.save.return_value = None
        u = LocalUploader()
        file = FileStorage(filename='test.jpg')
        res = u.upload_file(file)
        err_msg = ("Upload file should return True, \
                   as this extension is not allowed")
        assert res is True, err_msg

    @patch('werkzeug.datastructures.FileStorage.save', return_value=None)
    def test_local_uploader_upload_wrong_file(self, mock):
        """Test LOCAL UPLOADER upload works with wrong extension."""
        mock.save.return_value = None
        u = LocalUploader()
        file = FileStorage(filename='test.txt')
        res = u.upload_file(file)
        err_msg = ("Upload file should return False, \
                   as this extension is not allowed")
        assert res is False, err_msg
