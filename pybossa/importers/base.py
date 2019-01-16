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


class BulkImportException(Exception):

    """Generic Bulk Importer Exception Error."""

    def __init__(self, msg, err='error'):
        self.message = msg

    pass


class BulkTaskImport(object):

    """Class to import tasks in bulk."""

    importer_id = None

    def tasks(self):
        """Return a generator with all the tasks imported."""
        raise NotImplementedError

    def count_tasks(self):
        """Return amount of tasks to be imported."""
        return len([task for task in self.tasks()])

    def import_metadata(self):
        return None
