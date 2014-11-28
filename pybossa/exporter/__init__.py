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
# Cache global variables for timeouts
"""
Exporter module for exporting tasks and tasks results out of PyBossa
"""

import os
import zipfile
from pybossa.core import uploader
from pybossa.uploader import local, rackspace
from unidecode import unidecode
from flask import url_for, safe_join, send_file, redirect
from werkzeug.utils import secure_filename

class Exporter(object):

    """Abstract generic exporter class."""

    def _app_name_latin_encoded(self, app):
        """app short name for later HTML header usage"""
        # name = app.short_name.encode('utf-8', 'ignore').decode('latin-1')
        name = unidecode(app.short_name)
        return name

    def _zip_factory(self, filename):
        """create a ZipFile Object with compression and allow big ZIP files (allowZip64)"""
        try:
            import zlib
            zip_compression= zipfile.ZIP_DEFLATED
        except:
            zip_compression= zipfile.ZIP_STORED
        zip = zipfile.ZipFile(file=filename, mode='w', compression=zip_compression, allowZip64=True)
        return zip

    def _make_zip(self, app, ty):
        """Generate a ZIP of a certain type and upload it"""
        pass

    def _container(self, app):
        return "user_%d" % app.owner_id

    def _download_path(self, app):
        container = self._container(app)
        filepath = safe_join(uploader.upload_folder, container)
        return filepath

    def download_name(self, app, ty, format):
        """Get the filename (without) path of the file which should be downloaded.
           This function does not check if this filename actually exists!"""
        # TODO: Check if ty is valid
        name = self._app_name_latin_encoded(app)
        filename = '%s_%s_%s_%s.zip' % (str(app.id), name, ty, format)  # Example: 123_feynman_tasks_json.zip
        filename = secure_filename(filename)
        return filename

    def zip_existing(self, app, ty):
        """Check if exported ZIP is existing"""
        # TODO: Check ty
        filepath = self._download_path(app)
        filename=self.download_name(app, ty)
        if isinstance(uploader, local.LocalUploader):
            return os.path.isfile(safe_join(filepath, filename))
        else:
            return True
            # TODO: Check rackspace file existence

    def get_zip(self, app, ty):
        """Get a ZIP file directly from uploaded directory or generate one on the fly and upload it if not existing."""
        filepath = self._download_path(app)
        filename=self.download_name(app, ty)
        if not self.zip_existing(app, ty):
            print "Warning: Generating %s on the fly now!" % filename
            self._make_zip(app, ty)
        if isinstance(uploader, local.LocalUploader):
            res = send_file(filename_or_fp=safe_join(filepath, filename), mimetype='application/octet-stream', as_attachment=True, attachment_filename=filename)
            # fail safe mode for more encoded filenames.
            # It seems Flask and Werkzeug do not support RFC 5987 http://greenbytes.de/tech/tc2231/#encoding-2231-char
            # res.headers['Content-Disposition'] = 'attachment; filename*=%s' % filename
            return res
        else:
            return redirect(url_for('rackspace', filename=filename, container=self._container(app), _external=True))

    def response_zip(self, app, ty):
        return self.get_zip(app, ty)

    def pregenerate_zip_files(self, app):
        """Cache and generate all types (tasks and task_run) of ZIP files"""
        pass



