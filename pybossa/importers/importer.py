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
from .csv import BulkTaskCSVImport, BulkTaskGDImport
from .dropbox import BulkTaskDropboxImport
from .flickr import BulkTaskFlickrImport
from .twitterapi import BulkTaskTwitterImport
from .epicollect import BulkTaskEpiCollectPlusImport


class Importer(object):

    """Class to import data."""

    def __init__(self):
        """Init method."""
        self._importers = dict(csv=BulkTaskCSVImport,
                               gdocs=BulkTaskGDImport,
                               epicollect=BulkTaskEpiCollectPlusImport)
        self._importer_constructor_params = dict()

    def register_flickr_importer(self, flickr_params):
        """Register Flickr importer."""
        self._importers['flickr'] = BulkTaskFlickrImport
        self._importer_constructor_params['flickr'] = flickr_params

    def register_dropbox_importer(self):
        """Register Dropbox importer."""
        self._importers['dropbox'] = BulkTaskDropboxImport

    def register_twitter_importer(self, twitter_params):
        self._importers['twitter'] = BulkTaskTwitterImport
        self._importer_constructor_params['twitter'] = twitter_params

    def create_tasks(self, task_repo, project_id, **form_data):
        """Create tasks."""
        from pybossa.model.task import Task
        """Create tasks from a remote source using an importer object and
        avoiding the creation of repeated tasks"""
        empty = True
        n = 0
        last_task = None
        importer = self._create_importer_for(**form_data)
        for task_data in importer.tasks():
            task = Task(project_id=project_id)
            [setattr(task, k, v) for k, v in task_data.iteritems()]
            found = task_repo.get_task_by(project_id=project_id, info=task.info)
            if found is None:
                task_repo.save(task)
                n += 1
                empty = False
                last_task = task
        if empty:
            msg = gettext('It looks like there were no new records to import')
            return ImportReport(message=msg, last_task=last_task, total=n)
        msg = str(n) + " " + gettext('new tasks were imported successfully')
        if n == 1:
            msg = str(n) + " " + gettext('new task was imported successfully')
        report = ImportReport(message=msg, last_task=last_task, total=n)
        return report

    def count_tasks_to_import(self, **form_data):
        """Count tasks to import."""
        return self._create_importer_for(**form_data).count_tasks()

    def _create_importer_for(self, **form_data):
        """Create importer."""
        importer_id = form_data.get('type')
        params = self._importer_constructor_params.get(importer_id) or {}
        params.update(form_data)
        del params['type']
        return self._importers[importer_id](**params)

    def get_all_importer_names(self):
        """Get all importer names."""
        return self._importers.keys()

    def get_autoimporter_names(self):
        """Get autoimporter names."""
        return [name for name in self._importers.keys() if name != 'dropbox']


class ImportReport(object):

    def __init__(self, message, last_task, total):
        self._message = message
        self._last_task = last_task
        self._total = total

    @property
    def message(self):
        return self._message

    @property
    def last_task(self):
        return self._last_task

    @property
    def total(self):
        return self._total
