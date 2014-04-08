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
Local module for uploading files to a PyBossa local filesystem.

This module exports:
    * Local class: for uploading files to a local filesystem.

"""
from pybossa.uploader import Uploader
import os
from werkzeug import secure_filename


class LocalUploader(Uploader):

    """Local filesystem uploader class."""

    upload_folder = 'uploads'

    def __init__(self, upload_folder=None, **kwargs):
        """Init method to create a generic uploader."""
        if upload_folder:
            self.upload_folder = upload_folder
        super(self.__class__, self).__init__(**kwargs)

    def _upload_file(self, file):
        """Upload a file into a local folder."""
        try:
            filename = secure_filename(file.filename)
            file.save(os.path.join(self.upload_folder, filename))
            return True
        except:
            return False
