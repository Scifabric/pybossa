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

from flask.ext.babel import gettext
from .csv import _BulkTaskCSVImport, _BulkTaskGDImport
from .dropbox import _BulkTaskDropboxImport
from .flickr import _BulkTaskFlickrImport
from .twitterapi import _BulkTaskTwitterImport
from .epicollect import _BulkTaskEpiCollectPlusImport


class Importer(object):

    """Class to import data."""

    def __init__(self):
        """Init method."""
        self._importers = dict(csv=_BulkTaskCSVImport,
                               gdocs=_BulkTaskGDImport,
                               epicollect=_BulkTaskEpiCollectPlusImport)
        self._importer_constructor_params = dict()

    def register_flickr_importer(self, flickr_params):
        """Register Flickr importer."""
        self._importers['flickr'] = _BulkTaskFlickrImport
        self._importer_constructor_params['flickr'] = flickr_params

    def register_dropbox_importer(self):
        """Register Dropbox importer."""
        self._importers['dropbox'] = _BulkTaskDropboxImport

    def register_twitter_importer(self, twitter_params):
        self._importers['twitter'] = _BulkTaskTwitterImport
        self._importer_constructor_params['twitter'] = twitter_params

    def create_tasks(self, task_repo, project_id, **form_data):
        """Create tasks."""
        from pybossa.model.task import Task
        """Create tasks from a remote source using an importer object and
        avoiding the creation of repeated tasks"""
        empty = True
        n = 0
        importer = self._create_importer_for(**form_data)
        for task_data in importer.tasks():
            task = Task(project_id=project_id)
            [setattr(task, k, v) for k, v in task_data.iteritems()]
            found = task_repo.get_task_by(project_id=project_id, info=task.info)
            if found is None:
                task_repo.save(task)
                n += 1
                empty = False
        if empty:
            msg = gettext('It looks like there were no new records to import')
            return msg
        msg = str(n) + " " + gettext('new tasks were imported successfully')
        if n == 1:
            msg = str(n) + " " + gettext('new task was imported successfully')
        return msg

    def count_tasks_to_import(self, **form_data):
        """Count tasks to import."""
        return self._create_importer_for(**form_data).count_tasks()

    def _create_importer_for(self, **form_data):
        """Create importer."""
        importer_id = form_data.get('type')
        params = self._importer_constructor_params.get(importer_id) or {}
        params.update(form_data)
        return self._importers[importer_id](**params)

    def get_all_importer_names(self):
        """Get all importer names."""
        return self._importers.keys()

    def get_autoimporter_names(self):
        """Get autoimporter names."""
        return [name for name in self._importers.keys() if name != 'dropbox']
