# -*- coding: utf8 -*-
# This file is part of PyBossa.
#
# Copyright (C) 2015 SciFabric LTD.
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

class BulkImportException(Exception):

    """Generic Bulk Importer Exception Error."""

    pass


class _BulkTaskImport(object):

    """Class to import tasks in bulk."""

    importer_id = None

    def tasks(self, **form_data):
        """Return a generator with all the tasks imported."""
        pass

    def count_tasks(self, **form_data):
        """Return amount of tasks to be imported."""
        return len([task for task in self.tasks(**form_data)])