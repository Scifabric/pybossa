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

import json

from .base import BulkTaskImport


class BulkTaskDropboxImport(BulkTaskImport):

    """Class to import tasks from Dropbox in bulk."""

    importer_id = 'dropbox'

    def __init__(self, files, last_import_meta=None):
        self.files = files
        self.last_import_meta = last_import_meta

    def tasks(self):
        """Get tasks."""
        return [self._extract_file_info(_file) for _file in self.files]

    def count_tasks(self):
        """Count number of tasks."""
        return len(self.tasks())

    def _extract_file_info(self, _file):
        """Extract file information."""
        _file = json.loads(_file)
        info = {'filename': _file['name'],
                'link_raw': _file['link'].replace('dl=0', 'raw=1'),
                'link': _file['link']}
        if self._is_image_file(_file['name']):
            extra_fields = {'url_m': info['link_raw'],
                            'url_b': info['link_raw'],
                            'title': info['filename']}
            info.update(extra_fields)
        if self._is_video_file(_file['name']):
            url = self._create_raw_cors_link(_file['link'])
            extra_fields = {'video_url': url}
            info.update(extra_fields)
        if self._is_audio_file(_file['name']):
            url = self._create_raw_cors_link(_file['link'])
            extra_fields = {'audio_url': url}
            info.update(extra_fields)
        if self._is_pdf_file(_file['name']):
            url = self._create_raw_cors_link(_file['link'])
            extra_fields = {'pdf_url': url}
            info.update(extra_fields)
        return {'info': info}

    def _is_image_file(self, filename):
        """Check if it is an image."""
        return (filename.endswith('.png') or filename.endswith('.jpg') or
                filename.endswith('.jpeg') or filename.endswith('.gif'))

    def _is_video_file(self, filename):
        """Check if it is a video."""
        return (filename.endswith('.mp4') or filename.endswith('.m4v') or
                filename.endswith('.ogg') or filename.endswith('.ogv') or
                filename.endswith('.webm') or filename.endswith('.avi'))

    def _is_audio_file(self, filename):
        """Check if it is an audio."""
        return (filename.endswith('.mp4') or filename.endswith('.m4a') or
                filename.endswith('.ogg') or filename.endswith('.oga') or
                filename.endswith('.webm') or filename.endswith('.wav') or
                filename.endswith('.mp3'))

    def _is_pdf_file(self, filename):
        """Check if it is a PDF file."""
        return filename.endswith('.pdf')

    def _create_raw_cors_link(self, url):
        """Create RAW CORS link."""
        new_url = url.replace('www.dropbox.com',
                              'dl.dropboxusercontent.com')
        if new_url.endswith('?dl=0'):
            new_url = new_url[:-5]
        return new_url
