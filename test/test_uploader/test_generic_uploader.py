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

from default import Test, with_context
from pybossa.uploader import Uploader
from werkzeug.datastructures import FileStorage
from mock import patch
from PIL import Image
import tempfile
import os
from nose.tools import assert_raises


class TestUploader(Test):

    """Test PYBOSSA Uploader module."""

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

    @with_context
    def test_get_filename_extension(self):
        """Test UPLOADER get_filename_extension works."""
        u = Uploader()
        filename = "image.png"
        err_msg = "The extension should be PNG"
        assert u.get_filename_extension(filename) == 'png', err_msg
        filename = "image.jpg"
        err_msg = "The extension should be JPEG"
        assert u.get_filename_extension(filename) == 'jpeg', err_msg
        filename = "imagenoextension"
        err_msg = "The extension should be None"
        assert u.get_filename_extension(filename) == None, err_msg

    @with_context
    def test_crop(self):
        """Test UPLOADER crop works."""
        u = Uploader()
        size = (100, 100)
        im = Image.new('RGB', size)
        folder = tempfile.mkdtemp()
        u.upload_folder = folder
        im.save(os.path.join(folder, 'image.png'))
        coordinates = (0, 0, 50, 50)
        file = FileStorage(filename=os.path.join(folder, 'image.png'))
        with patch('pybossa.uploader.Image', return_value=True):
            err_msg = "It should crop the image"
            assert u.crop(file, coordinates) is True, err_msg

        with patch('pybossa.uploader.Image.open', side_effect=IOError):
            err_msg = "It should return false"
            assert u.crop(file, coordinates) is False, err_msg

    @with_context
    def test_external_url_handler(self):
        """Test UPLOADER external_url_handler works."""
        u = Uploader()
        with patch.object(u, '_lookup_url', return_value='url'):
            assert u.external_url_handler(BaseException, 'endpoint', 'values') == 'url'

    @with_context
    def test_external_url_handler_fails(self):
        """Test UPLOADER external_url_handler fails works."""
        u = Uploader()
        with patch.object(u, '_lookup_url', return_value=None):
            with patch('pybossa.uploader.sys') as mysys:
                mysys.exc_info.return_value=(BaseException, BaseException, None)
                assert_raises(BaseException,
                              u.external_url_handler,
                              BaseException,
                              'endpoint',
                              'values')

    @with_context
    def test_external_url_handler_fails_2(self):
        """Test UPLOADER external_url_handler fails works."""
        u = Uploader()
        with patch.object(u, '_lookup_url', return_value=None):
            with patch('pybossa.uploader.sys') as mysys:
                mysys.exc_info.return_value=(BaseException, BaseException, None)
                assert_raises(IOError,
                              u.external_url_handler,
                              IOError,
                              'endpoint',
                              'values')
