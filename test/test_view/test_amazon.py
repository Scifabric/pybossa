# -*- coding: utf8 -*-
# This file is part of PyBossa.
#
# Copyright (C) 2016 SciFabric LTD.
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
from mock import patch, MagicMock
from default import flask_app
from pybossa.s3_client import NoSuchBucket, PrivateBucket


class TestAmazonS3API(object):

    @patch('pybossa.view.amazon.S3Client')
    def test_buckets_with_specific_bucket_lists_its_content(self, S3Client):
        objects = ['test.pdf', 'sunset.png']
        bucket_name = 'Bucket1'
        client_instance = MagicMock()
        S3Client.return_value = client_instance
        client_instance.objects.return_value = objects

        resp = flask_app.test_client().get('/amazon/bucket/%s' % bucket_name)

        client_instance.objects.assert_called_with(bucket_name)
        assert resp.data == json.dumps(objects), resp.data

    @patch('pybossa.view.amazon.S3Client')
    def test_buckets_with_non_existing_bucket_returns_error(self, S3Client):
        client_instance = MagicMock()
        S3Client.return_value = client_instance
        client_instance.objects.side_effect = NoSuchBucket('Bucket "noSuchBucket" does not exist')

        resp = flask_app.test_client().get('/amazon/bucket/noSuchBucket')

        assert resp.status_code == 404, resp

    @patch('pybossa.view.amazon.S3Client')
    def test_buckets_with_private_bucket_returns_error(self, S3Client):
        client_instance = MagicMock()
        S3Client.return_value = client_instance
        client_instance.objects.side_effect = PrivateBucket('Bucket "noSuchBucket" is private')

        resp = flask_app.test_client().get('/amazon/bucket/privateBucket')

        assert resp.status_code == 403, resp
