# -*- coding: utf8 -*-
# This file is part of PYBOSSA.
#
# Copyright (C) 2015 Scifabric LTD.
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
"""This module tests the Uploader class."""

import os
import tempfile
from default import Test
from pybossa.uploader.local import LocalUploader
from mock import patch
from werkzeug.datastructures import FileStorage
from nose.tools import assert_raises

class TestLocalUploader(Test):

    """Test PYBOSSA Uploader module."""

    def test_local_uploader_relative_directory_init(self):
        """Test LOCAL UPLOADER init works with relative path."""
        new_upload_folder = 'uploads'
        new_config_uf = {'UPLOAD_FOLDER': new_upload_folder}
        with patch.dict(self.flask_app.config, new_config_uf):
            new_uploader = LocalUploader()
            new_uploader.init_app(self.flask_app)
            err_msg = "Upload folder should be absolute not relative"
            assert os.path.isabs(new_uploader.upload_folder) is True, err_msg
            err_msg = "Upload folder uploads should be existing"
            assert os.path.isdir(new_uploader.upload_folder) is True, err_msg

    def test_wrong_local_uploader_relative_directory_init(self):
        """Test LOCAL UPLOADER init with wrong relative path."""
        new_upload_folder = 'iamnotexisting'
        err_msg = "Uploadfolder ./iamnotexisting should not exist"
        assert os.path.isdir(new_upload_folder) is False, err_msg
        new_config_uf = {'UPLOAD_FOLDER': new_upload_folder}
        with patch.dict(self.flask_app.config, new_config_uf):
            new_uploader = LocalUploader()
            assert_raises(IOError, new_uploader.init_app, self.flask_app)   # Should raise IOError
            err_msg = "wrong upload folder ./iamnotexisting should not exist"
            assert os.path.isdir(new_upload_folder) is False, err_msg

    def test_local_uploader_standard_directory_existing(self):
        """Test if local uploads directory existing"""
        uploads_path = os.path.join(os.path.dirname(self.flask_app.root_path), 'uploads')   # ../uploads
        err_msg = "./uploads folder is not existing"
        assert os.path.isdir(uploads_path) is True, err_msg
        context_uploads_path = os.path.join(self.flask_app.root_path, 'uploads')            # pybossa/uploads
        err_msg = "pybossa/uploads should not exist"
        assert os.path.isdir(context_uploads_path) is False, err_msg

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
                err_msg = "Upload folder /tmp should be existing"
                assert os.path.isdir(new_uploader.upload_folder) is True, err_msg
                err_msg = "Upload folder by default is /tmp/"
                assert new_uploader.upload_folder == '/tmp/', err_msg

    @patch('werkzeug.datastructures.FileStorage.save', side_effect=IOError)
    def test_local_uploader_upload_fails(self, mock):
        """Test LOCAL UPLOADER upload fails."""
        u = LocalUploader()
        file = FileStorage(filename='test.jpg')
        res = u.upload_file(file, container='user_3')
        err_msg = ("Upload file should return False, \
                   as there is an exception")
        assert res is False, err_msg


    @patch('werkzeug.datastructures.FileStorage.save', return_value=None)
    def test_local_uploader_upload_correct_file(self, mock):
        """Test LOCAL UPLOADER upload works."""
        mock.save.return_value = None
        u = LocalUploader()
        file = FileStorage(filename='test.jpg')
        res = u.upload_file(file, container='user_3')
        err_msg = ("Upload file should return True, \
                   as this extension is allowed")
        assert res is True, err_msg

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

    @patch('werkzeug.datastructures.FileStorage.save', return_value=None)
    def test_local_folder_is_created(self, mock):
        """Test LOCAL UPLOADER folder creation works."""
        mock.save.return_value = True
        u = LocalUploader()
        u.upload_folder = tempfile.mkdtemp()
        file = FileStorage(filename='test.jpg')
        container = 'mycontainer'
        res = u.upload_file(file, container=container)
        path = os.path.join(u.upload_folder, container)
        err_msg = "This local path should exist: %s" % path
        assert os.path.isdir(path) is True, err_msg

    @patch('os.remove', return_value=None)
    def test_local_folder_delete(self, mock):
        """Test LOCAL UPLOADER delete works."""
        u = LocalUploader()
        err_msg = "Delete should return true"
        assert u.delete_file('file', 'container') is True, err_msg

    @patch('os.remove', side_effect=OSError)
    def test_local_folder_delete_fails(self, mock):
        """Test LOCAL UPLOADER delete fail works."""
        u = LocalUploader()
        err_msg = "Delete should return False"
        assert u.delete_file('file', 'container') is False, err_msg

    def test_file_exists_for_missing_file(self):
        """Test LOCAL UPLOADER file_exists returns False if the file does not exist"""
        u = LocalUploader()
        container = 'mycontainer'

        assert u.file_exists('noexist.txt', container) is False

    def test_file_exists_for_real_file(self):
        """Test LOCAL UPLOADER file_exists returns True if the file exists"""
        u = LocalUploader()
        u.upload_folder = tempfile.mkdtemp()
        file = FileStorage(filename='test.jpg')
        container = 'mycontainer'
        u.upload_file(file, container=container)

        assert u.file_exists('test.jpg', container) is True
