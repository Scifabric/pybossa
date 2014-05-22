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

from default import Test
from pybossa.uploader.rackspace import RackspaceUploader
from mock import patch, PropertyMock, call, MagicMock
from werkzeug.datastructures import FileStorage
from pyrax.fakes import FakeContainer
from pyrax.exceptions import NoSuchObject, NoSuchContainer
from test_uploader import cloudfiles_mock, fake_container


class TestRackspaceUploader(Test):

    """Test PyBossa Rackspace Uploader module."""

    @patch('pybossa.uploader.rackspace.pyrax.set_credentials',
           return_value=True)
    def test_rackspace_uploader_init(self, Mock):
        """Test RACKSPACE UPLOADER init works."""
        new_extensions = ['pdf', 'doe']
        with patch('pybossa.uploader.rackspace.pyrax.cloudfiles',
                   return_value=cloudfiles_mock):
            with patch.dict(self.flask_app.config,
                            {'ALLOWED_EXTENSIONS': new_extensions}):

                with patch('pybossa.uploader.rackspace.pyrax.cloudfiles') as mycf:
                    mycf.get_container.return_value = True
                    u = RackspaceUploader()
                    res = u.init_app(self.flask_app, cont_name='mycontainer')
                    err_msg = "It should return the container."
                    assert res is True, err_msg
                    err_msg = "The container name should be updated."
                    assert u.cont_name == 'mycontainer', err_msg
                    for ext in new_extensions:
                        err_msg = "The .%s extension should be allowed" % ext
                        assert ext in u.allowed_extensions, err_msg

    @patch('pybossa.uploader.rackspace.pyrax.set_credentials',
           return_value=True)
    @patch('pybossa.uploader.rackspace.pyrax.utils.get_checksum',
           return_value="1234abcd")
    def test_rackspace_uploader_creates_container(self, mock, mock2):
        """Test RACKSPACE UPLOADER creates container works."""
        with patch('pybossa.uploader.rackspace.pyrax.cloudfiles') as mycf:
            mycf.get_container.side_effect = NoSuchContainer
            mycf.create_container.return_value = True
            mycf.make_container_public.return_value = True
            u = RackspaceUploader()
            res = u.init_app(self.flask_app)
            err_msg = "Init app should return the container."
            assert res is True, err_msg


    @patch('pybossa.uploader.rackspace.pyrax.set_credentials',
           return_value=True)
    @patch('pybossa.uploader.rackspace.pyrax.utils.get_checksum',
           return_value="1234abcd")
    def test_rackspace_uploader_upload_correct_file(self, mock, mock2):
        """Test RACKSPACE UPLOADER upload file works."""
        with patch('pybossa.uploader.rackspace.pyrax.cloudfiles') as mycf:
            mycf.upload_file.return_value=True
            mycf.get_object.side_effect = NoSuchObject
            u = RackspaceUploader()
            u.init_app(self.flask_app)
            file = FileStorage(filename='test.jpg')
            err_msg = "Upload file should return True"
            assert u.upload_file(file, container='user_3') is True, err_msg
            calls = [call.get_container('user_3'),
                     call.get_container().get_object('test.jpg')]
            mycf.assert_has_calls(calls, any_order=True)

    @patch('pybossa.uploader.rackspace.pyrax.set_credentials',
           return_value=True)
    @patch('pybossa.uploader.rackspace.pyrax.utils.get_checksum',
           return_value="1234abcd")
    def test_rackspace_uploader_upload_correct_purgin_first_file(self, mock, mock2):
        """Test RACKSPACE UPLOADER upload file purging first file works."""
        with patch('pybossa.uploader.rackspace.pyrax.cloudfiles') as mycf:
            mycf.upload_file.return_value=True
            mycf.get_object.side_effect = True
            u = RackspaceUploader()
            u.init_app(self.flask_app)
            file = FileStorage(filename='test.jpg')
            err_msg = "Upload file should return True"
            assert u.upload_file(file, container='user_3') is True, err_msg
            calls = [call.get_container('user_3'),
                     call.get_container().get_object().delete(),
                     call.get_container().get_object('test.jpg')]
            print mycf.mock_calls
            mycf.assert_has_calls(calls, any_order=True)


    @patch('pybossa.uploader.rackspace.pyrax.set_credentials',
           return_value=True)
    @patch('pybossa.uploader.rackspace.pyrax.utils.get_checksum',
           return_value="1234abcd")
    def test_rackspace_uploader_upload_file_fails(self, mock, mock2):
        """Test RACKSPACE UPLOADER upload file fail works."""
        with patch('pybossa.uploader.rackspace.pyrax.cloudfiles') as mycf:
            from pyrax.exceptions import UploadFailed
            mycf.upload_file.side_effect = UploadFailed
            u = RackspaceUploader()
            u.init_app(self.flask_app)
            file = FileStorage(filename='test.jpg')
            err_msg = "Upload file should return False"
            assert u.upload_file(file, container='user_3') is False, err_msg

    @patch('pybossa.uploader.rackspace.pyrax.set_credentials',
           return_value=True)
    @patch('pybossa.uploader.rackspace.pyrax.utils.get_checksum',
           return_value="1234abcd")
    def test_rackspace_uploader_upload_file_object_fails(self, mock, mock2):
        """Test RACKSPACE UPLOADER upload file object fail works."""
        with patch('pybossa.uploader.rackspace.pyrax.cloudfiles') as mycf:
            from pyrax.exceptions import NoSuchObject
            container = MagicMock()
            container.get_object.side_effect = NoSuchObject
            mycf.get_container.return_value = container
            u = RackspaceUploader()
            u.init_app(self.flask_app)
            file = FileStorage(filename='test.jpg')
            err_msg = "Upload file should return True"
            assert u.upload_file(file, container='user_3') is True, err_msg

    @patch('pybossa.uploader.rackspace.pyrax.set_credentials',
           return_value=True)
    @patch('pybossa.uploader.rackspace.pyrax.utils.get_checksum',
           return_value="1234abcd")
    def test_rackspace_uploader_upload_wrong_file(self, mock, mock2):
        """Test RACKSPACE UPLOADER upload wrong file extension works."""
        with patch('pybossa.uploader.rackspace.pyrax.cloudfiles') as mycf:
            mycf.upload_file.return_value = True
            u = RackspaceUploader()
            u.init_app(self.flask_app)
            file = FileStorage(filename='test.docs')
            err_msg = "Upload file should return False"
            res = u.upload_file(file, container='user_3')
            assert res is False, err_msg

    @patch('pybossa.uploader.rackspace.pyrax.set_credentials',
           return_value=True)
    def test_rackspace_uploader_lookup_url(self, mock1):
        """Test RACKSPACE UPLOADER lookup returns a valid link."""
        uri = 'http://rackspace.com'
        filename = 'test.jpg'
        with patch('pybossa.uploader.rackspace.pyrax.cloudfiles') as mycf:
            cdn_enabled_mock = PropertyMock(return_value=True)
            type(fake_container).cdn_enabled = cdn_enabled_mock
            mycf.get_container.return_value = fake_container

            u = RackspaceUploader()
            u.init_app(self.flask_app)
            res = u._lookup_url('rackspace', {'filename': filename,
                                              'container': 'user_3'})
            expected_url = "%s/%s" % (uri, filename)
            print res
            err_msg = "We should get the following URL: %s" % expected_url
            assert res == expected_url, err_msg

    @patch('pybossa.uploader.rackspace.pyrax.set_credentials',
           return_value=True)
    def test_rackspace_uploader_lookup_url_none(self, mock1):
        """Test RACKSPACE UPLOADER lookup returns None for non enabled CDN."""
        filename = 'test.jpg'
        with patch('pybossa.uploader.rackspace.pyrax.cloudfiles') as mycf:
            cdn_enabled_mock = PropertyMock(return_value=False)
            type(fake_container).cdn_enabled = cdn_enabled_mock
            mycf.get_container.return_value = fake_container

            u = RackspaceUploader()
            u.init_app(self.flask_app)
            res = u._lookup_url('rackspace', {'filename': filename,
                                              'container': 'user_3'})
            err_msg = "We should get the None"
            assert res is None, err_msg

    @patch('pybossa.uploader.rackspace.pyrax.set_credentials',
           return_value=True)
    def test_rackspace_uploader_get_container(self, mock1):
        """Test RACKSPACE UPLOADER get_container method works."""
        with patch('pybossa.uploader.rackspace.pyrax.cloudfiles') as mycf:
            cdn_enabled_mock = PropertyMock(return_value=False)
            type(fake_container).cdn_enabled = cdn_enabled_mock
            mycf.get_container.side_effect = NoSuchContainer

            calls = [call.get_container('user_3'),
                     call.create_container('user_3'),
                     call.make_container_public('user_3')
                     ]
            u = RackspaceUploader()
            u.init_app(self.flask_app)
            assert u.get_container('user_3')
            mycf.assert_has_calls(calls, any_order=True)

    @patch('pybossa.uploader.rackspace.pyrax.set_credentials',
           return_value=True)
    def test_rackspace_uploader_delete(self, mock1):
        """Test RACKSPACE UPLOADER delete method works."""
        with patch('pybossa.uploader.rackspace.pyrax.cloudfiles') as mycf:
            calls = [call.get_container('container'),
                     call.get_container().get_object('file'),
                     call.get_container().get_object().delete()
                     ]
            u = RackspaceUploader()
            u.init_app(self.flask_app)
            err_msg = "It should return True"
            assert u.delete_file('file', 'container') is True, err_msg
            mycf.assert_has_calls(calls, any_order=True)

    @patch('pybossa.uploader.rackspace.pyrax.set_credentials',
           return_value=True)
    def test_rackspace_uploader_delete_fails(self, mock1):
        """Test RACKSPACE UPLOADER delete fails method works."""
        with patch('pybossa.uploader.rackspace.pyrax.cloudfiles') as mycf:
            container = MagicMock()
            container.get_object.side_effect = NoSuchObject
            mycf.get_container.return_value = container

            calls = [call.get_container('container'),
                     ]
            u = RackspaceUploader()
            u.init_app(self.flask_app)
            err_msg = "It should return False"
            assert u.delete_file('file', 'container') is False, err_msg
            mycf.assert_has_calls(calls, any_order=True)
