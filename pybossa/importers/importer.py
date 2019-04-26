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

from collections import defaultdict
from flask import current_app
from flask_babel import gettext
from .csv import BulkTaskCSVImport, BulkTaskGDImport, BulkTaskLocalCSVImport
from .dropbox import BulkTaskDropboxImport
from .flickr import BulkTaskFlickrImport
from .twitterapi import BulkTaskTwitterImport
from .youtubeapi import BulkTaskYoutubeImport
from .epicollect import BulkTaskEpiCollectPlusImport
from .iiif import BulkTaskIIIFImporter
from .s3 import BulkTaskS3Import
from .base import BulkImportException
from .usercsv import BulkUserCSVImport
from pybossa.util import check_password_strength, valid_or_no_s3_bucket
from flask_login import current_user
from werkzeug.datastructures import MultiDict
import copy
import json
from pybossa.util import delete_import_csv_file
from pybossa.cloud_store_api.s3 import upload_json_data
import hashlib
from flask import url_for
from pybossa.task_creator_helper import set_gold_answer, upload_files_priv


def validate_s3_bucket(task):
    valid = valid_or_no_s3_bucket(task.info)
    if not valid:
        current_app.logger.error('Invalid S3 bucket. project id: {}, task info: {}'.format(task.project_id, task.info))
    return valid


def validate_priority(task):
    if task.priority_0 is None:
        return True
    try:
        float(task.priority_0)
        return True
    except Exception:
        return False


def validate_n_answers(task):
    try:
        int(task.n_answers)
        return True
    except Exception:
        return False


class TaskImportValidator(object):

    validations = {
        'invalid priority': validate_priority,
        'invalid s3 bucket': validate_s3_bucket,
        'invalid n_answers': validate_n_answers
    }

    def __init__(self):
        self.errors = defaultdict(int)

    def validate(self, task):
        for error, validator in self.validations.items():
            if not validator(task):
                self.errors[error] += 1
                return False
        return True

    def add_error(self, key):
        self.errors[key] = self.errors.get(key, 0) + 1

    def __str__(self):
        msg = '{} task import failed due to {}.'
        return '\n'.join(msg.format(n, error) for error, n in self.errors.items())


class Importer(object):

    """Class to import data."""

    def __init__(self):
        """Init method."""
        self._importers = dict(csv=BulkTaskCSVImport,
                               gdocs=BulkTaskGDImport,
                               epicollect=BulkTaskEpiCollectPlusImport,
                               s3=BulkTaskS3Import,
                               localCSV=BulkTaskLocalCSVImport,
                               iiif=BulkTaskIIIFImporter)
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

    def upload_private_data(self, task, project_id):
        private_fields = task.pop('private_fields', None)
        if not private_fields:
            return
        file_name = 'task_private_data.json'
        task['info']['private_json__upload_url'] = upload_files_priv(task, project_id, private_fields, file_name)

    def create_tasks(self, task_repo, project, **form_data):
        """Create tasks."""
        from pybossa.model.task import Task
        """Create tasks from a remote source using an importer object and
        avoiding the creation of repeated tasks"""
        n = 0
        importer = self._create_importer_for(**form_data)
        tasks = importer.tasks()
        import_headers = importer.headers()
        mismatch_headers = []

        msg = ''
        if import_headers:
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

        validator = TaskImportValidator()
        n_answers = project.get_default_n_answers()
        for task_data in tasks:
            self.upload_private_data(task_data, project.id)
            task = Task(project_id=project.id, n_answers=n_answers)
            [setattr(task, k, v) for k, v in task_data.iteritems()]

            gold_answers = task_data.pop('gold_answers', None)
            set_gold_answer(task_data, project.id, gold_answers)

            found = task_repo.find_duplicate(project_id=project.id,
                                             info=task.info)
            if found is None:
                if validator.validate(task):
                    try:
                        task_repo.save(task)
                        n += 1
                    except Exception as e:
                        current_app.logger.exception(msg)
                        validator.add_error(str(e))

        if form_data.get('type') == 'localCSV':
            csv_filename = form_data.get('csv_filename')
            delete_import_csv_file(csv_filename)

        metadata = importer.import_metadata()
        if n==0:
            msg = gettext('It looks like there were no new records to import. ')
        elif n == 1:
            msg = str(n) + " " + gettext('new task was imported successfully ')
        else:
            msg = str(n) + " " + gettext('new tasks were imported successfully ')
        msg += str(validator)

        return ImportReport(message=msg, metadata=metadata, total=n)

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

    def delete_file(self, **form_data):
        self._create_importer_for(**form_data)._delete_file()

    def get_all_importer_names(self):
        """Get all importer names."""
        return self._importers.keys()

    def _create_user_form(self, user_data):
        from pybossa.view.account import get_project_choices
        from pybossa.forms.forms import RegisterFormWithUserPrefMetadata

        form_data = copy.deepcopy(user_data)
        upref = form_data.pop('user_pref', {})
        mdata = form_data.pop('metadata', {})

        if not isinstance(upref, dict):
            err = dict(user_pref='incorrect value')
            return False, err
        if not isinstance(mdata, dict) or \
            'user_type' not in mdata:
            err = dict(metadata='missing or incorrect user_type value')
            return False, err

        form_data['languages'] = upref.get('languages', [])
        form_data['locations'] = upref.get('locations', [])
        form_data['user_type'] = mdata.get('user_type')
        form_data.pop('info', None)
        form_data['confirm'] = user_data.get('password')
        form_data['project_slug'] = form_data.pop('project_slugs', [])

        form = RegisterFormWithUserPrefMetadata(MultiDict(form_data))
        form.generate_password()
        form.set_upref_mdata_choices()
        form.project_slug.choices = get_project_choices()
        return form

    def create_users(self, user_repo, **form_data):
        """Create users from a remote source using an importer object and
        avoiding the creation of repeated users"""

        from pybossa.view.account import create_account

        n = 0
        failed_users = 0
        invalid_values = set()
        importer = self._create_importer_for(**form_data)
        for user_data in importer.users():
            found = user_repo.search_by_email(email_addr=user_data['email_addr'].lower())
            if not found:
                full_name = user_data['fullname']
                project_slugs = user_data.get('project_slugs')
                form = self._create_user_form(user_data)
                if not form.validate():
                    failed_users += 1
                    current_app.logger.error(u'Failed to import user {}, {}'
                        .format(full_name, form.errors))
                    invalid_values.update(form.errors.keys())
                    continue
                user_data['metadata']['admin'] = current_user.name
                user_data['password'] = form.password.data
                create_account(user_data, project_slugs=project_slugs)
                n += 1
        if n > 0:
            msg = str(n) + " " + gettext('new users were imported successfully. ')
        else:
            msg = gettext('It looks like there were no new users created. ')

        if failed_users:
            msg += str(failed_users) + gettext(' user import failed for incorrect values of ') + ', '.join(invalid_values) + '.'
        return msg
