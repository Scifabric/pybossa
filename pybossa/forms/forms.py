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
from tempfile import NamedTemporaryFile

from flask import current_app
from flask import request
from flask_wtf import FlaskForm as Form
from flask_wtf.file import FileField, FileRequired, FileAllowed
from werkzeug.utils import secure_filename
from wtforms import IntegerField, DecimalField, TextField, BooleanField, \
    SelectField, validators, TextAreaField, PasswordField, FieldList, SelectMultipleField
from wtforms import SelectMultipleField
from wtforms.fields.html5 import EmailField, URLField
from wtforms.widgets import HiddenInput
from flask_babel import lazy_gettext

import validator as pb_validator
from pybossa import util
from pybossa.core import project_repo, user_repo, task_repo
from pybossa.core import uploader
from pybossa.uploader import local
from flask import safe_join
from flask_login import current_user
import os
import json
from decimal import Decimal

from pybossa.forms.fields.time_field import TimeField
from pybossa.forms.fields.select_two import Select2Field
from pybossa.sched import sched_variants
from validator import TimeFieldsValidator
from pybossa.core import enable_strong_password
from pybossa.util import get_file_path_for_import_csv
from flask import flash
import pybossa.data_access as data_access
import app_settings
import six
from iiif_prezi.loader import ManifestReader
from wtforms.validators import NumberRange

EMAIL_MAX_LENGTH = 254
USER_NAME_MAX_LENGTH = 35
USER_FULLNAME_MAX_LENGTH = 35
PROJECT_PWD_MIN_LEN = 5

def create_nullable_select(label, items):
    return SelectField(
        label=lazy_gettext(label),
        choices=[(None, "NONE")] + [(x,x) for x in items],
        coerce=lambda x: None if x == "None" else x
    )

### Custom Validators

def is_json(json_type):
    def v(form, field):
        try:
            assert isinstance(json.loads(field.data), json_type)
        except Exception:
            raise validators.ValidationError('Field must be JSON object.')
    return v

BooleanField.false_values = {False, 'false', '', 'off', 'n', 'no'}


class ProjectCommonForm(Form):
    name = TextField(lazy_gettext('Name'),
                     [validators.Required(),
                      pb_validator.Unique(project_repo.get_by, 'name',
                                          message=lazy_gettext("Name is already taken."))])

    short_name = TextField(lazy_gettext('Short Name'),
                           [validators.Required(),
                            pb_validator.NotAllowedChars(),
                            pb_validator.Unique(project_repo.get_by, 'short_name',
                                message=lazy_gettext(
                                    "Short Name is already taken.")),
                            pb_validator.ReservedName('project', current_app)])

    password = TextField(
                    lazy_gettext('Password'),
                    [validators.Required(),
                        pb_validator.CheckPasswordStrength(
                                        min_len=PROJECT_PWD_MIN_LEN,
                                        special=False)],
                    render_kw={'placeholder': 'Minimum length {} characters, 1 uppercase, 1 lowercase and 1 numeric.'.format(PROJECT_PWD_MIN_LEN)})

    def __init__(self, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)

class ProjectForm(ProjectCommonForm):

    long_description = TextAreaField(lazy_gettext('Long Description'),
                                     [validators.Required()])
    description = TextAreaField(lazy_gettext('Description'),
                                [validators.Length(max=255)])
    product = SelectField(lazy_gettext('Product'),
                          [validators.Required()], choices=[("", "")], default="")
    subproduct = SelectField(lazy_gettext('Subproduct'),
                             [validators.Required()], choices=[("", "")], default="")

    kpi = DecimalField(lazy_gettext('KPI - Estimate of amount of minutes to complete one task (0.1-120)'), places=2,
        validators=[validators.Required(), NumberRange(Decimal('0.1'), 120)])

class ProjectUpdateForm(ProjectForm):
    id = IntegerField(label=None, widget=HiddenInput())
    description = TextAreaField(lazy_gettext('Description'),
                            [validators.Required(
                                message=lazy_gettext(
                                    "You must provide a description.")),
                             validators.Length(max=255)])
    short_name = TextField(label=None, widget=HiddenInput())
    long_description = TextAreaField(lazy_gettext('Long Description'))
    allow_anonymous_contributors = BooleanField(lazy_gettext('Allow Anonymous Contributors'))
    zip_download = BooleanField(lazy_gettext('Allow ZIP data download'))
    category_id = SelectField(lazy_gettext('Category'), coerce=int)
    hidden = BooleanField(lazy_gettext('Hide?'))
    email_notif = BooleanField(lazy_gettext('Email Notifications'))
    password = TextField(
                    lazy_gettext('Password'),
                    [validators.Optional(),
                        pb_validator.CheckPasswordStrength(
                                        min_len=PROJECT_PWD_MIN_LEN,
                                        special=False)],
                    render_kw={'placeholder': 'Minimum length {} characters, 1 uppercase, 1 lowercase and 1 numeric.'.format(PROJECT_PWD_MIN_LEN)})
    webhook = TextField(lazy_gettext('Webhook'),
                        [pb_validator.Webhook()])
    sync_enabled = BooleanField(lazy_gettext('Enable Project Syncing'))

class AnnotationForm(Form):
    dataset_description = TextAreaField(lazy_gettext('Dataset Description'))
    provider = create_nullable_select(
        'Annotation Provider',
        ["PERSONNEL","VENDOR","CONTINGENT_WORKER","FREELANCER","CROWDSOURCING_WORKER"]
    )
    restrictions_and_permissioning = TextAreaField(lazy_gettext('Restrictions & Permissioning'))
    sampling_method = create_nullable_select(
        'Sampling Method',
        ["RANDOM","SYSTEMATIC","STRATIFIED","CLUSTERED"]
    )
    sampling_script = TextField(lazy_gettext('Sampling Script Link'))
    label_aggregation_strategy = create_nullable_select(
        'Label Aggregation Strategy',
        ["MAJORITY","WORKER_TRUST"]
    )
    task_input_schema = TextAreaField(lazy_gettext('Task Input Schema'))
    task_output_schema = TextAreaField(lazy_gettext('Task Output Schema'))

class ProjectSyncForm(Form):
    target_key = TextField(lazy_gettext('API Key'))


class ProjectQuizForm(Form):
    enabled = BooleanField(lazy_gettext('Enable Quiz Mode'))
    questions = IntegerField(
        lazy_gettext('Number of questions per quiz'),
        [
            validators.InputRequired(lazy_gettext('This field must be a positive integer.')),
            validators.NumberRange(min=1)
        ]
    )
    passing = IntegerField(
        lazy_gettext('Number of correct answers to pass quiz'),
        [
            validators.InputRequired(lazy_gettext('This field must be a non-negative integer.')),
            validators.NumberRange(min=0) # Making this 0 to allow quizzes with free-form answers.
        ]
    )
    completion_mode = SelectField(
        lazy_gettext('Completion mode'),
        choices=[
            ('all_questions', 'Present all the quiz questions'),
            ('short_circuit', 'End as soon as pass/fail status is known')
        ]
    )

    def validate_passing(form, field):
        correct = field.data
        total = form.questions.data
        if correct > total:
            raise validators.ValidationError(
                lazy_gettext(
                    'Correct answers required to pass (%(correct)d) is greater than the number of questions per quiz (%(total)d). \
                    It must be less than or equal to the number of questions per quiz.',
                    correct=correct,
                    total=total
                )
            )

class TaskPresenterForm(Form):
    id = IntegerField(label=None, widget=HiddenInput())
    editor = TextAreaField('')
    guidelines = TextAreaField('')

class TaskDefaultRedundancyForm(Form):
    default_n_answers = IntegerField(lazy_gettext('Default Redundancy'),
                           [validators.Required(),
                            validators.NumberRange(
                                min=task_repo.MIN_REDUNDANCY,
                                max=task_repo.MAX_REDUNDANCY,
                                message=lazy_gettext(
                                    'Number of answers should be a \
                                     value between {} and {:,}'.format(
                                        task_repo.MIN_REDUNDANCY,
                                        task_repo.MAX_REDUNDANCY
                                    )))])


class TaskRedundancyForm(Form):
    n_answers = IntegerField(lazy_gettext('Redundancy'),
                             [validators.Required(),
                              validators.NumberRange(
                                  min=task_repo.MIN_REDUNDANCY,
                                  max=task_repo.MAX_REDUNDANCY,
                                  message=lazy_gettext(
                                      'Number of answers should be a \
                                       value between {} and {:,}'.format(
                                          task_repo.MIN_REDUNDANCY,
                                          task_repo.MAX_REDUNDANCY
                                      )))])


class TaskPriorityForm(Form):
    task_ids = TextField(lazy_gettext('Task IDs'),
                         [validators.Required(),
                          pb_validator.CommaSeparatedIntegers()])

    priority_0 = DecimalField(lazy_gettext('Priority'),
                              [validators.NumberRange(
                                  min=0, max=1,
                                  message=lazy_gettext('Priority should be a \
                                                       value between 0.0 and 1.0'))])


class TaskTimeoutForm(Form):
    min_seconds = 30
    max_minutes = 120
    minutes = IntegerField(lazy_gettext('Minutes (default 60)'),
                           [validators.NumberRange(
                                min=0,
                                max=max_minutes
                            )])
    seconds = IntegerField(lazy_gettext('Seconds (0 to 59)'),
                           [validators.NumberRange(min=0, max=59)])

    def in_range(self):
        minutes = self.minutes.data or 0
        seconds = self.seconds.data or 0
        return self.min_seconds <= minutes*60 + seconds <= self.max_minutes*60



class TaskSchedulerForm(Form):
    _translate_names = lambda variant: (variant[0], lazy_gettext(variant[1]))
    _choices = map(_translate_names, sched_variants())
    sched = SelectField(lazy_gettext('Task Scheduler'), choices=_choices)
    rand_within_priority = BooleanField(lazy_gettext('Randomize Within Priority'))
    gold_task_probability_validator = validators.NumberRange(
        min=0,
        max=1,
        message=lazy_gettext('Gold task probability must be a value between 0.0 and 1.0')
    )
    gold_task_probability = DecimalField(
        label=lazy_gettext('Gold Probability'),
        validators=[gold_task_probability_validator],
        description=lazy_gettext('Probability value between 0 and 1')
    )

    @classmethod
    def update_sched_options(cls, new_options):
        _translate_names = lambda variant: (variant[0], lazy_gettext(variant[1]))
        _choices = map(_translate_names, new_options)
        cls.sched.kwargs['choices'] = _choices


class AnnouncementForm(Form):
    id = IntegerField(label=None, widget=HiddenInput())
    title = TextField(lazy_gettext('Title'),
                     [validators.Required(message=lazy_gettext(
                                    "You must enter a title for the post."))])
    body = TextAreaField(lazy_gettext('Body'),
                           [validators.Required(message=lazy_gettext(
                                    "You must enter some text for the post."))])
    info = TextField(lazy_gettext('Info'),
                       [validators.Required(message=lazy_gettext(
                                "You must enter a level for the post.")),
                       is_json(dict)])
    media_url = TextField(lazy_gettext('URL'))
    published = BooleanField(lazy_gettext('Publish'))


class BlogpostForm(Form):
    id = IntegerField(label=None, widget=HiddenInput())
    title = TextField(lazy_gettext('Title'),
                     [validators.Required(message=lazy_gettext(
                                    "You must enter a title for the post."))])
    body = TextAreaField(lazy_gettext('Body'),
                           [validators.Required(message=lazy_gettext(
                                    "You must enter some text for the post."))])
    published = BooleanField(lazy_gettext('Publish'))


class PasswordForm(Form):
    password = PasswordField(lazy_gettext('Password'),
                        [validators.Required(message=lazy_gettext(
                                    "You must enter a password"))])


class BulkTaskCSVImportForm(Form):
    form_name = TextField(label=None, widget=HiddenInput(), default='csv')
    msg_required = lazy_gettext("You must provide a URL")
    msg_url = lazy_gettext("Oops! That's not a valid URL. "
                           "You must provide a valid URL")
    csv_url = TextField(lazy_gettext('URL'),
                        [validators.Required(message=msg_required),
                         validators.URL(message=msg_url)])

    def get_import_data(self):
        return {'type': 'csv', 'csv_url': self.csv_url.data}


class BulkTaskGDImportForm(Form):
    form_name = TextField(label=None, widget=HiddenInput(), default='gdocs')
    msg_required = lazy_gettext("You must provide a URL")
    msg_url = lazy_gettext("Oops! That's not a valid URL. "
                           "You must provide a valid URL")
    googledocs_url = TextField(lazy_gettext('URL'),
                               [validators.Required(message=msg_required),
                                   validators.URL(message=msg_url)])

    def get_import_data(self):
        return {'type': 'gdocs', 'googledocs_url': self.googledocs_url.data}


class BulkTaskLocalCSVImportForm(Form):
    form_name = TextField(label=None, widget=HiddenInput(), default='localCSV')
    do_not_validate_tp = BooleanField(
        label=lazy_gettext("Do not require all fields used in task presenter code to be present in the csv file"),
        default=False
    )

    _allowed_extensions = set(['csv'])
    def _allowed_file(self, filename):
        return '.' in filename and \
            filename.rsplit('.', 1)[1] in self._allowed_extensions

    def _container(self):
        return "user_%d" % current_user.id

    def _upload_path(self):
        container = self._container()
        filepath = None
        if isinstance(uploader, local.LocalUploader):
            filepath = safe_join(uploader.upload_folder, container)
            if not os.path.isdir(filepath):
                os.makedirs(filepath)
            return filepath

        current_app.logger.error('Failed to generate upload path {0}'.format(filepath))
        raise IOError('Local Upload folder is missing: {0}'.format(filepath))

    def get_import_data(self):
        def get_csv_filename():
            if request.method != 'POST':
                return
            if 'file' not in request.files:
                return
            csv_file = request.files['file']
            if csv_file.filename == '':
                return
            if csv_file and self._allowed_file(csv_file.filename):
                return get_file_path_for_import_csv(csv_file)

        return {
            'type': 'localCSV',
            'csv_filename': get_csv_filename(),
            'validate_tp': not self.do_not_validate_tp.data
        }


class BulkTaskEpiCollectPlusImportForm(Form):
    form_name = TextField(label=None, widget=HiddenInput(), default='epicollect')
    msg_required = lazy_gettext("You must provide an EpiCollect Plus "
                                "project name")
    msg_form_required = lazy_gettext("You must provide a Form name "
                                     "for the project")
    epicollect_project = TextField(lazy_gettext('Project Name'),
                                   [validators.Required(message=msg_required)])
    epicollect_form = TextField(lazy_gettext('Form name'),
                                [validators.Required(message=msg_required)])

    def get_import_data(self):
        return {'type': 'epicollect',
                'epicollect_project': self.epicollect_project.data,
                'epicollect_form': self.epicollect_form.data}


class BulkTaskFlickrImportForm(Form):
    form_name = TextField(label=None, widget=HiddenInput(), default='flickr')
    msg_required = lazy_gettext("You must provide a valid Flickr album ID")
    album_id = TextField(lazy_gettext('Album ID'),
                         [validators.Required(message=msg_required)])
    def get_import_data(self):
        return {'type': 'flickr', 'album_id': self.album_id.data}


class BulkTaskDropboxImportForm(Form):
    form_name = TextField(label=None, widget=HiddenInput(), default='dropbox')
    files = FieldList(TextField(label=None, widget=HiddenInput()))
    def get_import_data(self):
        return {'type': 'dropbox', 'files': self.files.data}


class BulkTaskTwitterImportForm(Form):
    form_name = TextField(label=None, widget=HiddenInput(), default='twitter')
    msg_required = lazy_gettext("You must provide some source for the tweets")
    source = TextField(lazy_gettext('Source'),
                       [validators.Required(message=msg_required)])
    max_tweets = IntegerField(lazy_gettext('Number of tweets'))
    user_credentials = TextField(label=None)
    def get_import_data(self):
        return {
            'type': 'twitter',
            'source': self.source.data,
            'max_tweets': self.max_tweets.data,
            'user_credentials': self.user_credentials.data,
        }


class BulkTaskYoutubeImportForm(Form):
    form_name = TextField(label=None, widget=HiddenInput(), default='youtube')
    msg_required = lazy_gettext("You must provide a valid playlist")
    playlist_url = URLField(lazy_gettext('Playlist'),
                             [validators.Required(message=msg_required)])
    def get_import_data(self):
        return {
          'type': 'youtube',
          'playlist_url': self.playlist_url.data
        }

class BulkTaskS3ImportForm(Form):
    form_name = TextField(label=None, widget=HiddenInput(), default='s3')
    files = FieldList(TextField(label=None, widget=HiddenInput()))
    msg_required = lazy_gettext("You must provide a valid bucket")
    bucket = TextField(lazy_gettext('Bucket'),
                       [validators.Required(message=msg_required)])
    def get_import_data(self):
        return {
            'type': 's3',
            'files': self.files.data,
            'bucket': self.bucket.data
        }

class BulkTaskIIIFImportForm(Form):
    form_name = TextField(label=None, widget=HiddenInput(), default='iiif')
    msg_required = lazy_gettext("You must provide a URL")
    msg_url = lazy_gettext("Oops! That's not a valid URL. "
                           "You must provide a valid URL")
    manifest_uri = TextField(lazy_gettext('URL'),
                             [validators.Required(message=msg_required),
                             validators.URL(message=msg_url)])
    version = SelectField(lazy_gettext('Presentation API version'), choices=[
        (ctx, ctx) for ctx in ManifestReader.contexts
    ], default='2.1')

    def get_import_data(self):
        return {
            'type': 'iiif',
            'manifest_uri': self.manifest_uri.data,
            'version': self.version.data
        }


class GenericBulkTaskImportForm(object):
    """Callable class that will return, when called, the appropriate form
    instance"""
    _forms = {
        'csv': BulkTaskCSVImportForm,
        'gdocs': BulkTaskGDImportForm,
        'epicollect': BulkTaskEpiCollectPlusImportForm,
        'flickr': BulkTaskFlickrImportForm,
        'dropbox': BulkTaskDropboxImportForm,
        'twitter': BulkTaskTwitterImportForm,
        's3': BulkTaskS3ImportForm,
        'youtube': BulkTaskYoutubeImportForm,
        'localCSV': BulkTaskLocalCSVImportForm,
        'iiif': BulkTaskIIIFImportForm
    }

    def __call__(self, form_name, *form_args, **form_kwargs):
        if form_name is None:
            return None
        return self._forms[form_name](*form_args, **form_kwargs)


### Forms for account view

class LoginForm(Form):

    """Login Form class for signin into PYBOSSA."""

    email = TextField(lazy_gettext('E-mail'),
                      [validators.Required(
                          message=lazy_gettext("The e-mail is required"))])

    password = PasswordField(lazy_gettext('Password'),
                             [validators.Required(
                                 message=lazy_gettext(
                                     "You must provide a password"))])


class RegisterForm(Form):

    """Register Form Class for creating an account in PYBOSSA."""

    err_msg = lazy_gettext("Full name must be between 3 and %(fullname)s "
                           "characters long", fullname=USER_FULLNAME_MAX_LENGTH)
    fullname = TextField(lazy_gettext('Full name'),
                         [validators.Length(min=3, max=USER_FULLNAME_MAX_LENGTH, message=err_msg)])

    err_msg = lazy_gettext("User name must be between 3 and %(username_length)s "
                           "characters long", username_length=USER_NAME_MAX_LENGTH)
    err_msg_2 = lazy_gettext("The user name is already taken")
    name = TextField(lazy_gettext('User name'),
                         [
                          validators.Length(min=3, max=USER_NAME_MAX_LENGTH, message=err_msg),
                          pb_validator.NotAllowedChars(),
                          pb_validator.Unique(user_repo.get_by, 'name', err_msg_2),
                          pb_validator.ReservedName('account', current_app)])

    err_msg = lazy_gettext("Email must be between 3 and %(email_length)s "
                           "characters long", email_length=EMAIL_MAX_LENGTH)
    err_msg_2 = lazy_gettext("Email is already taken")
    email_addr = EmailField(lazy_gettext('Email Address'),
                           [validators.Length(min=3,
                                              max=EMAIL_MAX_LENGTH,
                                              message=err_msg),
                            validators.Email(),
                            pb_validator.UniqueCaseInsensitive(
                                user_repo.search_by_email,
                                'email_addr',
                                err_msg_2)])

    err_msg = lazy_gettext("Password cannot be empty")
    err_msg_2 = lazy_gettext("Passwords must match")
    if enable_strong_password:
        password = PasswordField(
                        lazy_gettext('New Password'),
                        [validators.Required(err_msg),
                         validators.EqualTo('confirm', err_msg_2),
                         pb_validator.CheckPasswordStrength()])
    else:
        password = PasswordField(
                        lazy_gettext('New Password'),
                        [validators.Required(err_msg),
                            validators.EqualTo('confirm', err_msg_2)])

    confirm = PasswordField(lazy_gettext('Repeat Password'))
    project_slug = SelectMultipleField(lazy_gettext('Project'), choices=[])
    consent = BooleanField(default='checked', false_values=("False", "false", '', '0', 0))

    def generate_password(self):
        if self.data['password']:
            return
        password = util.generate_password()
        self.password.data = password
        self.confirm.data = password


class UpdateProfileForm(Form):

    """Form Class for updating PYBOSSA's user Profile."""

    id = IntegerField(label=None, widget=HiddenInput())

    err_msg = lazy_gettext("Full name must be between 3 and %(fullname)s "
                           "characters long" , fullname=USER_FULLNAME_MAX_LENGTH)
    fullname = TextField(lazy_gettext('Full name'),
                         [validators.Length(min=3, max=USER_FULLNAME_MAX_LENGTH, message=err_msg)])

    err_msg = lazy_gettext("User name must be between 3 and %(username_length)s "
                           "characters long", username_length=USER_NAME_MAX_LENGTH)
    err_msg_2 = lazy_gettext("The user name is already taken")
    name = TextField(lazy_gettext('Username'),
                     [validators.Length(min=3, max=USER_NAME_MAX_LENGTH, message=err_msg),
                      pb_validator.NotAllowedChars(),
                      pb_validator.Unique(user_repo.get_by, 'name', err_msg_2),
                      pb_validator.ReservedName('account', current_app)])

    err_msg = lazy_gettext("Email must be between 3 and %(email_length)s "
                           "characters long", email_length=EMAIL_MAX_LENGTH)
    err_msg_2 = lazy_gettext("Email is already taken")
    email_addr = EmailField(lazy_gettext('Email Address'),
                           [validators.Length(min=3,
                                              max=EMAIL_MAX_LENGTH,
                                              message=err_msg),
                            validators.Email(),
                            pb_validator.Unique(user_repo.get_by, 'email_addr', err_msg_2)])
    subscribed = BooleanField(lazy_gettext('Get email notifications'))

    locale = SelectField(lazy_gettext('Language'))
    ckan_api = TextField(lazy_gettext('CKAN API Key'))
    privacy_mode = BooleanField(lazy_gettext('Privacy Mode'))
    restrict = BooleanField(lazy_gettext('Restrict processing'))

    def set_locales(self, locales):
        """Fill the locale.choices."""
        choices = []
        for locale in locales:
            choices.append(locale)
        self.locale.choices = choices


class ChangePasswordForm(Form):

    """Form for changing user's password."""

    current_password = PasswordField(lazy_gettext('Current password'))

    err_msg = lazy_gettext("Password cannot be empty")
    err_msg_2 = lazy_gettext("Passwords must match")
    if enable_strong_password:
        new_password = PasswordField(
                        lazy_gettext('New Password'),
                        [validators.Required(err_msg),
                            pb_validator.CheckPasswordStrength(),
                            validators.EqualTo('confirm', err_msg_2)])
    else:
        new_password = PasswordField(
                        lazy_gettext('New password'),
                        [validators.Required(err_msg),
                            validators.EqualTo('confirm', err_msg_2)])
    confirm = PasswordField(lazy_gettext('Repeat password'))


class ResetPasswordForm(Form):

    """Class for resetting user's password."""

    err_msg = lazy_gettext("Password cannot be empty")
    err_msg_2 = lazy_gettext("Passwords must match")
    if enable_strong_password:
        new_password = PasswordField(
                        lazy_gettext('New Password'),
                        [validators.Required(err_msg),
                            pb_validator.CheckPasswordStrength(),
                            validators.EqualTo('confirm', err_msg_2)])
    else:
        new_password = PasswordField(
                        lazy_gettext('New Password'),
                        [validators.Required(err_msg),
                            validators.EqualTo('confirm', err_msg_2)])
    confirm = PasswordField(lazy_gettext('Repeat Password'))


class ForgotPasswordForm(Form):

    """Form Class for forgotten password."""

    err_msg = lazy_gettext("Email must be between 3 and %(email_length)s "
                           "characters long", email_length=EMAIL_MAX_LENGTH)
    email_addr = EmailField(lazy_gettext('Email Address'),
                           [validators.Length(min=3,
                                              max=EMAIL_MAX_LENGTH,
                                              message=err_msg),
                            validators.Email()])


class PasswordResetKeyForm(Form):
    password_reset_key = TextAreaField(lazy_gettext('Password Reset Key'),
                                       [validators.Required(message=lazy_gettext(
                                        'You must provide the Password Reset Key.'))])


class OTPForm(Form):
    otp = TextField(lazy_gettext('One Time Password'),
                    [validators.Required(message=lazy_gettext(
                        'You must provide a valid OTP code'))])


### Forms for admin view

class SearchForm(Form):
    user = TextField(lazy_gettext('User'))


class CategoryForm(Form):
    id = IntegerField(label=None, widget=HiddenInput())
    name = TextField(lazy_gettext('Name'),
                     [validators.Required(),
                      pb_validator.Unique(project_repo.get_category_by, 'name',
                                          message="Name is already taken.")])
    description = TextField(lazy_gettext('Description'),
                            [validators.Required()])


### Common forms
class AvatarUploadForm(Form):
    id = IntegerField(label=None, widget=HiddenInput())
    avatar = FileField(lazy_gettext('Avatar'),
                       validators=[FileRequired(),
                                   FileAllowed(['png', 'jpg', 'jpeg', 'gif'])])
    x1 = IntegerField(label=None, widget=HiddenInput(), default=0)
    y1 = IntegerField(label=None, widget=HiddenInput(), default=0)
    x2 = IntegerField(label=None, widget=HiddenInput(), default=0)
    y2 = IntegerField(label=None, widget=HiddenInput(), default=0)


class BulkUserCSVImportForm(Form):
    form_name = TextField(label=None, widget=HiddenInput(), default='usercsvimport')
    _allowed_extensions = set(['csv'])
    def _allowed_file(self, filename):
        return '.' in filename and \
            filename.rsplit('.', 1)[1] in self._allowed_extensions

    def get_import_data(self):
        if request.method == 'POST':
            if 'file' not in request.files:
                flash('No file part')
                return {'type': 'usercsvimport', 'csv_filename': None}
            csv_file = request.files['file']
            if csv_file.filename == '':
                flash('No file selected')
                return {'type': 'usercsvimport', 'csv_filename': None}
            if csv_file and self._allowed_file(csv_file.filename):
                with NamedTemporaryFile(delete=False) as tmpfile:
                    csv_file.save(tmpfile)
                return {'type': 'usercsvimport', 'csv_filename': tmpfile.name}
        return {'type': 'usercsvimport', 'csv_filename': None}


class GenericUserImportForm(object):
    """Callable class that will return, when called, the appropriate form
    instance"""
    _forms = {'usercsvimport': BulkUserCSVImportForm}

    def __call__(self, form_name, *form_args, **form_kwargs):
        if form_name is None:
            return None
        return self._forms[form_name](*form_args, **form_kwargs)


class UserPrefMetadataForm(Form):
    """Form for admins to add metadata for users or for users to update their
    own metadata"""
    languages = Select2Field(
        lazy_gettext('Language(s)'), choices=[],default="")
    locations = Select2Field(
        lazy_gettext('Location(s)'), choices=[], default="")
    work_hours_from = TimeField(
        lazy_gettext('Work Hours From'),
        [TimeFieldsValidator(["work_hours_to", "timezone"],
        message="Work Hours From, Work Hours To, and Timezone must be filled out for submission")],
        default='')
    work_hours_to = TimeField(
        lazy_gettext('Work Hours To'),
        [TimeFieldsValidator(["work_hours_from", "timezone"],
        message="Work Hours From, Work Hours To, and Timezone must be filled out for submission")],
        default='')
    timezone = SelectField(lazy_gettext('Timezone'),
        [TimeFieldsValidator(["work_hours_from", "work_hours_to"],
        message="Work Hours From, Work Hours To, and Timezone must be filled out for submission")],
        choices=[], default="")
    user_type = SelectField(
        lazy_gettext('Type of user'), [validators.Required()], choices=[], default="")
    if data_access.data_access_levels:
        data_access = Select2Field(
            lazy_gettext('Data Access(s)'), [validators.Required(),
                pb_validator.UserTypeValiadator()],
            choices=data_access.data_access_levels['valid_access_levels'], default="")
    review = TextAreaField(
        lazy_gettext('Additional comments'), default="")

    def __init__(self, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)
        self.set_can_update(kwargs.get('can_update', (True, None)))

    def set_upref_mdata_choices(self):
        upref_mdata_choices = app_settings.upref_mdata.get_upref_mdata_choices()
        self.languages.choices = upref_mdata_choices['languages']
        self.locations.choices = upref_mdata_choices['locations']
        self.timezone.choices = upref_mdata_choices['timezones']
        self.user_type.choices = upref_mdata_choices['user_types']

    def set_can_update(self, can_update_info):
        self._disabled = self._get_disabled_fields(can_update_info)

    def _get_disabled_fields(self, (can_update, disabled_fields)):
        if not can_update:
            return {field: 'Form is not updatable.' for field in self}
        return {getattr(self, name): reason for name, reason in six.iteritems(disabled_fields or {})}

    def is_disabled(self, field):
        return self._disabled.get(field, False)

class TransferOwnershipForm(Form):
    email_addr = EmailField(lazy_gettext('Email of the new owner'))


class RegisterFormWithUserPrefMetadata(RegisterForm, UserPrefMetadataForm):
    """Create User Form that has ability to set user preferences and metadata"""
    consent = BooleanField(default='checked', false_values=("False", "false", '', '0', 0))


class DataAccessForm(Form):
    """Form to configure data access levels"""

    #for future extensions
