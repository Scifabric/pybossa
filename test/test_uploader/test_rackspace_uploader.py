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
from pybossa.uploader.rackspace import RackspaceUploader
from mock import patch, PropertyMock
from werkzeug.datastructures import FileStorage
from pyrax.fakes import FakeContainer


class TestRackspaceUploader:

    """Test PyBossa Rackspace Uploader module."""


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

    @patch('pybossa.uploader.rackspace.pyrax.set_credentials',
           return_value=True)
    def test_rackspace_uploader_init(self, Mock):
        """Test RACKSPACE UPLOADER init works."""
        new_extensions = set(['pdf', 'doe'])
        with patch('pybossa.uploader.rackspace.pyrax.cloudfiles.get_container',
                   return_value='pybossa'):
            u = RackspaceUploader("username",
                                  "apikey",
                                  "ORD",
                                  allowed_extensions=new_extensions)
            for ext in new_extensions:
                err_msg = "The .%s extension should be allowed" % ext
                assert ext in u.allowed_extensions, err_msg

    @patch('pybossa.uploader.rackspace.pyrax.set_credentials',
           return_value=True)
    @patch('pybossa.uploader.rackspace.pyrax.utils.get_checksum',
           return_value="1234abcd")
    def test_rackspace_uploader_upload_correct_file(self, mock, mock2):
        """Test RACKSPACE UPLOADER upload file works."""
        with patch('pybossa.uploader.rackspace.pyrax.cloudfiles.upload_file',
                   return_value=True):
            u = RackspaceUploader("username",
                                  "apikey",
                                  "ORD")
            file = FileStorage(filename='test.jpg')
            err_msg = "Upload file should return True"
            assert u.upload_file(file) is True, err_msg

    @patch('pybossa.uploader.rackspace.pyrax.set_credentials',
           return_value=True)
    @patch('pybossa.uploader.rackspace.pyrax.utils.get_checksum',
           return_value="1234abcd")
    def test_rackspace_uploader_upload_wrong_file(self, mock, mock2):
        """Test RACKSPACE UPLOADER upload wrong file extension works."""
        with patch('pybossa.uploader.rackspace.pyrax.cloudfiles.upload_file',
                   return_value=True):
            u = RackspaceUploader("username",
                                  "apikey",
                                  "ORD")
            file = FileStorage(filename='test.docs')
            err_msg = "Upload file should return False"
            res = u.upload_file(file)
            print res
            assert res is False, err_msg

    @patch('pybossa.uploader.rackspace.pyrax.set_credentials',
           return_value=True)
    def test_rackspace_uploader_lookup_url(self, mock1):
        """Test RACKSPACE UPLOADER lookup returns a valid link."""
        uri = 'http://rackspace.com'
        with patch('pyrax.fakes.FakeContainer.cdn_enabled', new_callable=PropertyMock) as mock_cdn_enabled:
            mock_cdn_enabled.return_value = True
            with patch('pyrax.fakes.FakeContainer.cdn_uri', new_callable=PropertyMock) as mock_cdn_uri:
                mock_cdn_uri.return_value = uri
                fake_container = FakeContainer('a', 'b', 0, 0)
                filename = 'test.jpg'
                with patch('pybossa.uploader.rackspace.pyrax.cloudfiles.get_container',
                           return_value=fake_container):

                    u = RackspaceUploader("username",
                                          "apikey",
                                          "ORD")
                    res = u._lookup_url('rackspace', {'filename': filename})
                    expected_url = "%s/%s" % (uri, filename)
                    err_msg = "We should get the following URL: %s" % expected_url
                    assert res == expected_url, err_msg

    @patch('pybossa.uploader.rackspace.pyrax.set_credentials',
           return_value=True)
    def test_rackspace_uploader_lookup_url_none(self, mock1):
        """Test RACKSPACE UPLOADER lookup returns None for non enabled CDN."""
        uri = 'http://rackspace.com'
        with patch('pyrax.fakes.FakeContainer.cdn_enabled', new_callable=PropertyMock) as mock_cdn_enabled:
            mock_cdn_enabled.return_value = False
            fake_container = FakeContainer('a', 'b', 0, 0)
            #fake_container.cdn_enabled = True
            filename = 'test.jpg'
            with patch('pybossa.uploader.rackspace.pyrax.cloudfiles.get_container',
                       return_value=fake_container):

                u = RackspaceUploader("username",
                                      "apikey",
                                      "ORD")
                res = u._lookup_url('rackspace', {'filename': filename})
                err_msg = "We should get the None"
                assert res is None, err_msg
