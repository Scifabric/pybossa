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
from pybossa.uploader.local import LocalUploader
from mock import patch
from werkzeug.datastructures import FileStorage


class TestLocalUploader(Test):

    """Test PyBossa Uploader module."""

    @with_context
    def test_local_uploader_init(self):
        """Test LOCAL UPLOADER init works."""
        u = LocalUploader()
        u.init_app(self.flask_app)
        new_extensions = ['pdf', 'doe']
        new_upload_folder = '/tmp/'
        new_config_ext = {'ALLOWED_EXTENSIONS': new_extensions}
        new_config_uf = {'UPLOAD_FOLDER': new_upload_folder}
        with patch.dict(self.flask_app.config, new_config_ext):
            with patch.dict(self.flask_app.config, new_config_uf):
                new_uploader = LocalUploader()
                new_uploader.init_app(self.flask_app)
                expected_extensions = set.union(u.allowed_extensions,
                                                new_extensions)
                err_msg = "The new uploader should support two extra extensions"
                assert expected_extensions == new_uploader.allowed_extensions, err_msg
                err_msg = "Upload folder by default is /tmp/"
                assert new_uploader.upload_folder == '/tmp/', err_msg

    @with_context
    @patch('werkzeug.datastructures.FileStorage.save', return_value=None)
    def test_local_uploader_upload_correct_file(self, mock):
        """Test LOCAL UPLOADER upload works."""
        mock.save.return_value = None
        u = LocalUploader()
        file = FileStorage(filename='test.jpg')
        res = u.upload_file(file, container='user_3')
        err_msg = ("Upload file should return True, \
                   as this extension is not allowed")
        assert res is True, err_msg

    @with_context
    @patch('werkzeug.datastructures.FileStorage.save', return_value=None)
    def test_local_uploader_upload_wrong_file(self, mock):
        """Test LOCAL UPLOADER upload works with wrong extension."""
        mock.save.return_value = None
        u = LocalUploader()
        file = FileStorage(filename='test.txt')
        res = u.upload_file(file, container='user_3')
        err_msg = ("Upload file should return False, \
                   as this extension is not allowed")
        assert res is False, err_msg
