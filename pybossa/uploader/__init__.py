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


class Uploader(object):

    """Generic uploader class."""

    allowed_extensions = set(['js', 'css', 'png', 'jpg', 'jpeg', 'gif'])

    def __init__(self, allowed_extensions=None):
        """Init method to create a generic uploader."""
        if allowed_extensions:
            self.allowed_extensions = set.union(self.allowed_extensions,
                                                allowed_extensions)

    def allowed_file(self, filename):
        """Return filename if valid, otherwise false."""
        return '.' in filename and \
            filename.rsplit('.', 1)[1] in self.allowed_extensions

    def upload_file(self):
        """Override by teh uploader handler: local, cloud, etc."""
        pass

    def external_url_handler(self):
        """Override by teh uploader handler: local, cloud, etc."""
        pass
