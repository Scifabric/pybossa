# -*- coding: utf8 -*-
# This file is part of PyBossa.
#
# Copyright (C) 2016 SciFabric LTD.
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

from .base import BulkTaskImport


class BulkTaskS3Import(BulkTaskImport):

    """Class to import tasks from Flickr in bulk."""

    importer_id = "amazon_s3"

    def __init__(self, api_key, album_id, last_import_meta=None):
        pass

    def tasks(self):
        return []

    def count_tasks(self):
        return 0

