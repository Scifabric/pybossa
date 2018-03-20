# -*- coding: utf8 -*-
# This file is part of PYBOSSA.
#
# Copyright (C) 2018 Scifabric LTD.
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

import json
from mock import patch
from nose.tools import *
from pybossa.importers import BulkImportException
from pybossa.importers.iiif import BulkTaskIIIFImporter
from default import FakeResponse, with_context

@patch('pybossa.importers.iiif.requests')
class TestBulkTaskIIIFImport(object):

    def setUp(self):
        self.manifest_uri = 'http://example.org/iiif/book1/manifest'
        self.canvas_id_base = 'http://example.org/iiif/book1/canvas/p'
        self.img_id_base = 'http://example.org/images/book1-page'
        self.importer = BulkTaskIIIFImporter(manifest_uri=self.manifest_uri)

    def create_manifest(self, sequences=1):
        manifest = {
            '@id': self.manifest_uri,
            'sequences': [
                {
                    'canvases': []
                }
            ]
        }
        for i in range(sequences):
            canvas = {
                '@id': self.canvas_id_base.format(i),
                'images': [
                    {
                        'resource': {
                            'service': {
                                '@id': self.img_id_base.format(i)
                            }
                        }
                    }
                ]
            }
            manifest['sequences'][0]['canvases'].append(canvas)
        return manifest

    def test_task_count_returns_1_for_valid_manifest(self, requests):
        headers = {'Content-Type': 'application/json'}
        wrapper = {
            'okay': 1,
            'received': json.dumps(self.create_manifest())
        }
        valid_manifest = FakeResponse(text=json.dumps(wrapper),
                                      status_code=200, headers=headers,
                                      encoding='utf-8')
        requests.get.return_value = valid_manifest
        count = self.importer.count_tasks()
        assert_equal(count, 1)

    def test_task_count_raises_exception_for_invalid_manifest(self, requests):
        headers = {'Content-Type': 'application/json'}
        wrapper = {
            'okay': 0,
            'received': 'Something else'
        }
        invalid_manifest = FakeResponse(text=json.dumps(wrapper),
                                        status_code=200, headers=headers,
                                        encoding='utf-8')
        requests.get.return_value = invalid_manifest
        msg = "Oops! That doesn't look like a valid IIIF manifest."

        assert_raises(BulkImportException, self.importer.count_tasks)
        try:
            self.importer.count_tasks()
        except BulkImportException as e:
            assert e[0] == msg, e

    @with_context
    def test_get_tasks_raises_exception_for_invalid_manifest(self, requests):
        headers = {'Content-Type': 'application/json'}
        wrapper = {
            'okay': 0,
            'received': 'Something else'
        }
        invalid_manifest = FakeResponse(text=json.dumps(wrapper),
                                        status_code=200, headers=headers,
                                        encoding='utf-8')
        requests.get.return_value = invalid_manifest
        msg = "Oops! That doesn't look like a valid IIIF manifest."

        assert_raises(BulkImportException, self.importer.count_tasks)
        try:
            self.importer.tasks()
        except BulkImportException as e:
            assert e[0] == msg, e

    @with_context
    def test_get_tasks_for_valid_manifest(self, requests):
        n = 3
        headers = {'Content-Type': 'application/json'}
        wrapper = {
            'okay': 1,
            'received': json.dumps(self.create_manifest(n))
        }
        valid_manifest = FakeResponse(text=json.dumps(wrapper),
                                      status_code=200, headers=headers,
                                      encoding='utf-8')
        requests.get.return_value = valid_manifest
        tasks = self.importer.tasks()

        assert_equal(len(tasks), n)
        for i, task in enumerate(tasks):
            canvas_id = self.canvas_id_base.format(i)
            img_id = self.img_id_base.format(i)
            link_query = '?manifest={}#?cv={}'.format(self.manifest_uri, i)
            link = 'http://universalviewer.io/uv.html' + link_query
            assert_dict_equal(task['info'], {
                'manifest': self.manifest_uri,
                'target': canvas_id,
                'link': link,
                'tileSource': '{}/info.json'.format(img_id),
                'url': '{}/full/max/0/default.jpg'.format(img_id),
                'url_m': '{}/full/240,/0/default.jpg'.format(img_id),
                'url_b': '{}/full/1024,/0/default.jpg'.format(img_id)
            })

    def test_validated_manifest_returned_as_json(self, requests):
        headers = {'Content-Type': 'application/json'}
        wrapper = {
            'okay': 1,
            'received': json.dumps(self.create_manifest())
        }
        valid_manifest = FakeResponse(text=json.dumps(wrapper),
                                      status_code=200, headers=headers,
                                      encoding='utf-8')
        requests.get.return_value = valid_manifest
        returned_manifest = self.importer._get_validated_manifest(None)
        assert_equal(type(returned_manifest), dict)
