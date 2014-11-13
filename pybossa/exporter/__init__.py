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

import zipfile


class Exporter(object):

    """Generic exporter class."""

    def __init__(self):
        """Init method to create a generic uploader."""
        pass    # nothing special needed yet

    def justatest(self):
        print "Hallo Test123!!!!!!!"

    def _zip_factory(self, filename):
        try:
            import zlib
            zip_compression= zipfile.ZIP_DEFLATED
        except:
            zip_compression= zipfile.ZIP_STORED
        zip = zipfile.ZipFile(file=filename, mode='w', compression=zip_compression, allowZip64=True)
        return zip

    def _upload_zip(self, app, ty):
        """Generate a ZIP of a certain type and upload it"""
        pass

    def get_zip(self, app, ty):
        """Get a ZIP file directly from uploaded directory or generate one on the fly and upload it if not existing."""
        pass

    def get_zip_filename(self, app, ty):
        pass

    def response_zip(self, app, ty):
        pass

    def pregenerate_zips(self, app):
        """Cache and generate all types (tasks and task_run) of ZIP files"""
        pass



