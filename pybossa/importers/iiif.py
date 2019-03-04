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
import requests
from iiif_prezi.loader import ManifestReader

from .base import BulkTaskImport, BulkImportException


class BulkTaskIIIFImporter(BulkTaskImport):
    """Class to import tasks from IIIF manifests."""

    importer_id = "iiif"

    def __init__(self, manifest_uri, version='2.1'):
        """Init method."""
        self.manifest_uri = manifest_uri
        self.version = version

    def tasks(self):
        """Get tasks."""
        return self._generate_tasks()

    def count_tasks(self):
        """Count number of tasks."""
        return len(self.tasks())

    def _generate_tasks(self):
        """Generate the tasks."""
        manifest = self._get_validated_manifest(self.manifest_uri,
                                                self.version)
        task_data = self._get_task_data(manifest)
        return [dict(info=data) for data in task_data]

    def _get_task_data(self, manifest):
        """Return the task data generated from a manifest."""
        manifest_uri = manifest['@id']
        canvases = manifest['sequences'][0]['canvases']

        data = []
        for i, canvas in enumerate(canvases):
            images = [img['resource']['service']['@id']
                      for img in canvas['images']]

            for img in images:
                row = {
                    'tileSource': '{}/info.json'.format(img),
                    'target': canvas['@id'],
                    'manifest': manifest_uri,
                    'link': self._get_link(manifest_uri, i),
                    'url': '{}/full/max/0/default.jpg'.format(img),
                    'url_m': '{}/full/240,/0/default.jpg'.format(img),
                    'url_b': '{}/full/1024,/0/default.jpg'.format(img)
                }
                data.append(row)
        return data

    def _get_link(self, manifest_uri, canvas_index):
        """Return a Universal Viewer URL for sharing."""
        base = 'http://universalviewer.io/uv.html'
        query = '?manifest={}#?cv={}'.format(manifest_uri, canvas_index)
        return base + query

    def _get_validated_manifest(self, manifest_uri, version):
        """Return a validated manifest."""
        r = requests.get(manifest_uri)
        if r.status_code != 200:
            err_msg = 'Invalid manifest URI: {} error'.format(r.status_code)
            raise BulkImportException(err_msg)
        reader = ManifestReader(r.text, version=version)
        try:
            mf = reader.read()
            mf_json = mf.toJSON()
        except Exception as e:
            raise BulkImportException(str(e))
        return mf_json
