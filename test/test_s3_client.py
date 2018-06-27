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

from mock import patch, MagicMock
from nose.tools import assert_raises
import json
from pybossa.s3_client import S3Client, NoSuchBucket, PrivateBucket

class TestS3Client(object):

    def make_response(self, text, status_code=200):
        fake_response = MagicMock()
        fake_response.text = text
        fake_response.status_code = status_code
        return fake_response

    bucket_with_content = (
     """<?xml version="1.0" encoding="UTF-8"?>
        <ListBucketResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/">
            <Name>test-pybossa</Name>
            <Prefix></Prefix>
            <Marker></Marker>
            <MaxKeys>1000</MaxKeys>
            <IsTruncated>false</IsTruncated>
            <Contents>
                <Key>16535035993_1080p.mp4</Key>
                <LastModified>2016-01-29T08:55:41.000Z</LastModified>
                <ETag>&quot;10055dfebe62cf30e34d87fd27b28efc&quot;</ETag>
                <Size>11801468</Size>
                <StorageClass>STANDARD</StorageClass>
            </Contents>
            <Contents>
                <Key>BFI-demo.mp4</Key>
                <LastModified>2016-01-29T08:55:38.000Z</LastModified>
                <ETag>&quot;b24442a1484b6b8f2b4e08c43e0abd3f&quot;</ETag>
                <Size>27063915</Size>
                <StorageClass>STANDARD</StorageClass>
            </Contents>
        </ListBucketResult>
        """)

    empty_bucket = (
     """<?xml version="1.0" encoding="UTF-8"?>
        <ListBucketResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/">
            <Name>test-pybossa</Name>
            <Prefix></Prefix>
            <Marker></Marker>
            <MaxKeys>1000</MaxKeys>
            <IsTruncated>false</IsTruncated>
        </ListBucketResult>
        """)

    no_such_bucket = (
     """<?xml version="1.0" encoding="UTF-8"?>
        <Error>
            <Code>NoSuchBucket</Code>
            <Message>The specified bucket does not exist</Message>
            <BucketName>test-pybosa</BucketName>
            <RequestId>5DB95818E2273F2A</RequestId>
            <HostId>2xqg6pMK20zocCIN0DpqzDVEmbNkqKdTrp0BT/K2EUBbSIek5+7333DjDVuvpN0fFR/Pp/+IkM8=</HostId>
        </Error>
        """)

    bucket_with_folder = (
     """<?xml version="1.0" encoding="UTF-8"?>
        <ListBucketResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/">
            <Name>test-pybossa</Name>
            <Prefix></Prefix>
            <Marker></Marker>
            <MaxKeys>1000</MaxKeys>
            <IsTruncated>false</IsTruncated>
            <Contents>
                <Key>myfolder/</Key>
                <LastModified>2016-01-29T08:56:15.000Z</LastModified>
                <ETag>&quot;d41d8cd98f00b204e9800998ecf8427e&quot;</ETag>
                <Size>0</Size>
                <StorageClass>STANDARD</StorageClass>
            </Contents>
        </ListBucketResult>
        """)

    private_bucket = (
     """<?xml version="1.0" encoding="UTF-8"?>
        <Error>
            <Code>AccessDenied</Code>
            <Message>Access Denied</Message>
            <RequestId>0C189C667703869B</RequestId>
            <HostId>e6HNleTSx+vQHCXsjphJNLumbwd2YfYfZMrEBEkGOF/0jCMDZf6RIrgUAooa+HT86f0Azr27/h4=</HostId>
        </Error>
        """)

    @patch('pybossa.s3_client.requests')
    def test_objects_return_empty_list_for_an_empty_bucket(self, requests):
        resp = self.make_response(self.empty_bucket, 200)
        requests.get.return_value = resp

        objects = S3Client().objects('test-pybossa')

        assert objects == [], objects

    @patch('pybossa.s3_client.requests')
    def test_objects_return_list_of_object_names_in_a_bucket(self, requests):
        resp = self.make_response(self.bucket_with_content, 200)
        requests.get.return_value = resp

        objects = S3Client().objects('test-pybossa')

        assert objects == ['16535035993_1080p.mp4', 'BFI-demo.mp4'], objects

    @patch('pybossa.s3_client.requests')
    def test_objects_not_returns_folders_inside_bucket(self, requests):
        resp = self.make_response(self.bucket_with_folder, 200)
        requests.get.return_value = resp

        objects = S3Client().objects('test-pybossa')

        assert objects == [], objects

    @patch('pybossa.s3_client.requests')
    def test_objects_raises_NoSuchBucket_if_bucket_does_not_exist(self, requests):
        resp = self.make_response(self.no_such_bucket, 404)
        requests.get.return_value = resp

        assert_raises(NoSuchBucket, S3Client().objects, 'test-pybossa')

    @patch('pybossa.s3_client.requests')
    def test_objects_raises_PrivateBucket_if_bucket_is_private(self, requests):
        resp = self.make_response(self.no_such_bucket, 403)
        requests.get.return_value = resp

        assert_raises(PrivateBucket, S3Client().objects, 'test-pybossa')
