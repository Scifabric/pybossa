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

from flask import current_app
from flask.ext.babel import gettext
from .csv import BulkTaskCSVImport, BulkTaskGDImport, BulkTaskLocalCSVImport
from .dropbox import BulkTaskDropboxImport
from .flickr import BulkTaskFlickrImport
from .twitterapi import BulkTaskTwitterImport
from .youtubeapi import BulkTaskYoutubeImport
from .epicollect import BulkTaskEpiCollectPlusImport
from .s3 import BulkTaskS3Import
from .base import BulkImportException
from .usercsv import BulkUserCSVImport
from flask import current_app
from pybossa.util import check_password_strength, valid_or_no_s3_bucket

class Importer(object):

    """Class to import data."""

    def __init__(self):
        """Init method."""
        self._importers = dict(csv=BulkTaskCSVImport,
                               gdocs=BulkTaskGDImport,
                               epicollect=BulkTaskEpiCollectPlusImport,
                               s3=BulkTaskS3Import,
                               localCSV=BulkTaskLocalCSVImport)
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

    def register_youtube_importer(self, youtube_params):
        self._importers['youtube'] = BulkTaskYoutubeImport
        self._importer_constructor_params['youtube'] = youtube_params

    def create_tasks(self, task_repo, project, **form_data):
        """Create tasks."""
        from pybossa.model.task import Task
        """Create tasks from a remote source using an importer object and
        avoiding the creation of repeated tasks"""
        empty = True
        n = 0
        importer = self._create_importer_for(**form_data)
        tasks = importer.tasks()
        import_headers = importer.headers()
        mismatch_headers = []

        if import_headers:
            msg = None
            if not project:
                msg = gettext('Could not load project info')
            else:
                task_presenter_headers = project.get_presenter_headers()
                mismatch_headers = [header for header in task_presenter_headers
                                    if header not in import_headers]

            if mismatch_headers:
                msg = 'Imported columns do not match task presenter code. '
                additional_msg = 'Mismatched columns: {}'.format((', '.join(mismatch_headers))[:80])
                current_app.logger.error(msg)
                current_app.logger.error(', '.join(mismatch_headers))
                msg += additional_msg

            if msg:
                # Failed validation
                current_app.logger.error(msg)
                return ImportReport(message=msg, metadata=None, total=0)

        s3_bucket_failures = 0
        for task_data in tasks:
            task = Task(project_id=project.id)
            [setattr(task, k, v) for k, v in task_data.iteritems()]
            found = task_repo.find_duplicate(project_id=project.id,
                                             info=task.info)
            if found is None:
                if valid_or_no_s3_bucket(task.info):
                    task_repo.save(task)
                    n += 1
                    empty = False
                else:
                    s3_bucket_failures += 1
                    current_app.logger.error('Invalid S3 bucket. project id: {}, task info: {}'.format(project.id, task.info))

        additional_msg = ' {} task import failed due to invalid S3 bucket.'\
                            .format(s3_bucket_failures) if s3_bucket_failures else ''
        if form_data.get('type') == 'localCSV':
            s3_url = form_data.get('csv_filename')
            importer.delete_local_csv_import_s3_file(s3_url)

        if empty:
            msg = gettext('It looks like there were no new records to import.')
            msg += additional_msg
            return ImportReport(message=msg, metadata=None, total=n)
        metadata = importer.import_metadata()
        msg = str(n) + " " + gettext('new tasks were imported successfully ')
        if n == 1:
            msg = str(n) + " " + gettext('new task was imported successfully ')
        msg += additional_msg

        report = ImportReport(message=msg, metadata=metadata, total=n)
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
        no_autoimporters = ('dropbox', 's3')
        return [name for name in self._importers.keys() if name not in no_autoimporters]

    def set_importers(self, importers):
        self._importers = \
            {key: val for key, val in self._importers.iteritems()
             if key in importers}


class ImportReport(object):

    def __init__(self, message, metadata, total):
        self._message = message
        self._metadata = metadata
        self._total = total

    @property
    def message(self):
        return self._message

    @property
    def metadata(self):
        return self._metadata

    @property
    def total(self):
        return self._total


class UserImporter(object):

    """Class to import data."""

    def __init__(self):
        """Init method."""
        self._importers = dict(usercsvimport=BulkUserCSVImport)
        self._importer_constructor_params = dict()

    def count_users_to_import(self, **form_data):
        """Count number of users to import."""
        return self._create_importer_for(**form_data).count_users()

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

    def create_users(self, user_repo, **form_data):
        """Create users from a remote source using an importer object and
        avoiding the creation of repeated users"""

        from pybossa.view.account import create_account
        n = 0
        failcount = 0
        importer = self._create_importer_for(**form_data)
        failed_user_imports =[]
        for user_data in importer.users():
            try:
                found = user_repo.search_by_email(email_addr=user_data['email_addr'].lower())
                if not found:
                    password = user_data['password']
                    is_password_valid, message = check_password_strength(password)
                    if not is_password_valid:
                        failed_user_imports.append(user_data['fullname'])
                        failcount += 1
                    else:
                        project_slugs = user_data['project_slugs'].split()
                        create_account(user_data, project_slugs=project_slugs)
                        n += 1
            except Exception:
                current_app.logger.exception('Error in create_user')
        if n > 0:
            msg = str(n) + " " + gettext('new users were imported successfully.')
        else:
            msg = gettext('It looks like there were no new users created.')
        if failcount > 0:
            msg += str(failcount) + gettext(' user(s) could not be imported due to weak password.')
            current_app.logger.error('Failed to import users due to password mismatch: {0}'.format(",".join(failed_user_imports)))
        return msg
