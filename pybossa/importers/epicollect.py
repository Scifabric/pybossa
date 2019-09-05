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

import json
import requests
from flask_babel import gettext

from .base import BulkTaskImport, BulkImportException


class BulkTaskEpiCollectPlusImport(BulkTaskImport):

    """Class to import tasks in bulk from an EpiCollect+ project."""

    importer_id = "epicollect"

    def __init__(self, epicollect_project,
                 epicollect_form, last_import_meta=None):
        BulkTaskImport.__init__(self)
        self.project = epicollect_project
        self.form = epicollect_form
        self.last_import_meta = last_import_meta

    def tasks(self):
        """Get tasks."""
        dataurl = self._get_data_url()
        r = requests.get(dataurl)
        return self._get_epicollect_data_from_request(r)

    def _import_epicollect_tasks(self, data):
        """Import epicollect tasks."""
        for d in data:
            yield {"info": d}

    def _get_data_url(self):
        """Get data url."""
        return 'http://plus.epicollect.net/%s/%s.json' % \
            (self.project, self.form)

    def _get_epicollect_data_from_request(self, r):
        """Get epicollect data from request."""
        if r.status_code == 403:
            msg = ("Oops! It looks like you don't have permission to access"
                   " the EpiCollect Plus project")
            raise BulkImportException(gettext(msg), 'error')
        if 'application/json' not in r.headers['content-type']:
            msg = "Oops! That project and form do not look like the right one."
            raise BulkImportException(gettext(msg), 'error')
        return self._import_epicollect_tasks(json.loads(r.text))
