# -*- coding: utf8 -*-
# This file is part of PYBOSSA.
#
# Copyright (C) 2016 Scifabric LTD.
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

from .base import BulkTaskImport


class BulkTaskS3Import(BulkTaskImport):

    """Class to import tasks from Flickr in bulk."""

    importer_id = "s3"

    def __init__(self, files, bucket, last_import_meta=None):
        BulkTaskImport.__init__(self)
        self.files = files
        self.bucket = bucket
        self.last_import_meta = last_import_meta

    def tasks(self):
        return [self._create_task_info(filename) for filename in self.files]

    def count_tasks(self):
        return len(self.tasks())

    def _create_task_info(self, filename):
        url = 'https://%s.s3.amazonaws.com/%s' % (self.bucket, filename)
        info = {'filename': filename,
                'url': url,
                'link': url}
        if self._is_image_file(filename):
            extra_fields = {'url_m': url,
                            'url_b': url,
                            'title': filename}
            info.update(extra_fields)
        if self._is_video_file(filename):
            extra_fields = {'video_url': url}
            info.update(extra_fields)
        if self._is_audio_file(filename):
            extra_fields = {'audio_url': url}
            info.update(extra_fields)
        if self._is_pdf_file(filename):
            extra_fields = {'pdf_url': url}
            info.update(extra_fields)
        return {'info': info}

    def _is_image_file(self, filename):
        return (filename.endswith('.png') or filename.endswith('.jpg') or
                filename.endswith('.jpeg') or filename.endswith('.gif'))

    def _is_video_file(self, filename):
        return (filename.endswith('.mp4') or filename.endswith('.m4v') or
                filename.endswith('.ogg') or filename.endswith('.ogv') or
                filename.endswith('.webm') or filename.endswith('.avi'))

    def _is_audio_file(self, filename):
        return (filename.endswith('.mp4') or filename.endswith('.m4a') or
                filename.endswith('.ogg') or filename.endswith('.oga') or
                filename.endswith('.webm') or filename.endswith('.wav') or
                filename.endswith('.mp3'))

    def _is_pdf_file(self, filename):
        return filename.endswith('.pdf')

