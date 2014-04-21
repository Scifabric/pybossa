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
Uploader module for uploading files to PyBossa.

This module exports:
    * Uploader class: for uploading files.

"""
import sys


class Uploader(object):

    """Generic uploader class."""

    allowed_extensions = set(['js', 'css', 'png', 'jpg', 'jpeg', 'gif'])

    def __init__(self, app=None):
        """Init method to create a generic uploader."""
        self.app = app
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        """Config allowed extensions."""
        if app.config.get('ALLOWED_EXTENSIONS'):
            self.allowed_extensions = set.union(self.allowed_extensions,
                                                set(app.config['ALLOWED_EXTENSIONS']))

    def _lookup_url(self, endpoint, values):
        """Override by the uploader handler."""
        pass

    def _upload_file(self, file):
        """Override by the specific uploader handler."""
        pass

    def allowed_file(self, filename):
        """Return True if valid, otherwise false."""
        return '.' in filename and \
            filename.rsplit('.', 1)[1].lower() in self.allowed_extensions

    def upload_file(self, file):
        """Override by teh uploader handler: local, cloud, etc."""
        if file and self.allowed_file(file.filename):
            return self._upload_file(file)
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
                raise exc_type, exc_value, tb
            else:
                raise error
        # url_for will use this result, instead of raising BuildError.
        return url
