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
# Cache global variables for timeouts
"""
Uploader module for uploading files to PYBOSSA.

This module exports:
    * Uploader class: for uploading files.

"""
import sys
from PIL import Image


class Uploader(object):

    """Generic uploader class."""

    allowed_extensions = set(['js', 'css', 'png', 'jpg', 'jpeg', 'gif', 'zip'])
    size = 512, 512

    def __init__(self, app=None):
        """Init method to create a generic uploader."""
        self.app = app
        if app is not None: # pragma: no cover
            self.init_app(app)

    def init_app(self, app):
        """Config allowed extensions."""
        if app.config.get('ALLOWED_EXTENSIONS'):
            self.allowed_extensions = set.union(self.allowed_extensions,
                                                set(app.config['ALLOWED_EXTENSIONS']))

    def _lookup_url(self, endpoint, values): # pragma: no cover
        """Override by the uploader handler."""
        pass

    def _upload_file(self, file, container): # pragma: no cover
        """Override by the specific uploader handler."""
        pass

    def get_filename_extension(self, filename):
        """Return filename extension."""
        try:
            extension = filename.rsplit('.', 1)[1].lower()
            if extension == 'jpg':
                extension = 'jpeg'
            return extension
        except:
            return None

    def crop(self, file, coordinates):
        """Crop filename and overwrite it."""
        try:
            filename = file.filename
            extension = self.get_filename_extension(filename)
            from io import BytesIO
            m = BytesIO()
            im = Image.open(file)
            if coordinates != (0, 0, 0, 0):
                target = im.crop(coordinates)
            else:
                target = im
            target.save(m, format=extension)
            file.stream = m
            file.stream.seek(0)
            return True
        except:
            return False


    def allowed_file(self, filename):
        """Return True if valid, otherwise false."""
        return '.' in filename and \
            filename.rsplit('.', 1)[1].lower() in self.allowed_extensions

    def upload_file(self, file, container, coordinates=None):
        """Override by the uploader handler: local, cloud, etc."""
        if file and self.allowed_file(file.filename):
            if coordinates: # pragma: no cover
                self.crop(file, coordinates)
            return self._upload_file(file, container)
        else:
            return False

    def external_url_handler(self, error, endpoint, values):
        """Build up an external URL when url_for cannot build a URL."""
        # This is an example of hooking the build_error_handler.
        # Here, lookup_url is some utility function you've built
        # which looks up the endpoint in some external URL registry.
        url = self._lookup_url(endpoint, values)
        if url is None:
            # External lookup did not have a URL.
            # Re-raise the BuildError, in context of original traceback.
            exc_type, exc_value, tb = sys.exc_info()
            if exc_value is error:
                raise exc_type(exc_value).with_traceback(tb)
            else:
                raise error
        # url_for will use this result, instead of raising BuildError.
        return url

    def delete_file(self, name, container):  # pragma: no cover
        """Override by the uploader handler."""
        pass

    def file_exists(self, name, container):  #pragma: no cover
        """Override by the uploader handler."""
        pass
