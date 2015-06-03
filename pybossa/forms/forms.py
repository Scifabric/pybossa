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

from flask import current_app
from flask_wtf import Form
from flask_wtf.file import FileField, FileRequired
from wtforms import IntegerField, DecimalField, TextField, BooleanField, \
    SelectField, validators, TextAreaField, PasswordField, FieldList
from wtforms.fields.html5 import EmailField
from wtforms.widgets import HiddenInput
from flask.ext.babel import lazy_gettext, gettext

from pybossa.core import project_repo, user_repo
from pybossa.sched import sched_variants
import validator as pb_validator


EMAIL_MAX_LENGTH = 254
USER_NAME_MAX_LENGTH = 35
USER_FULLNAME_MAX_LENGTH = 35

### Forms for projects view

class ProjectForm(Form):
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
    long_description = TextAreaField(lazy_gettext('Long Description'),
                                     [validators.Required()])


class ProjectUpdateForm(ProjectForm):
    id = IntegerField(label=None, widget=HiddenInput())
    description = TextAreaField(lazy_gettext('Description'),
                            [validators.Required(
                                message=lazy_gettext(
                                    "You must provide a description.")),
                             validators.Length(max=255)])
    long_description = TextAreaField(lazy_gettext('Long Description'))
    allow_anonymous_contributors = SelectField(
        lazy_gettext('Allow Anonymous Contributors'),
        choices=[('True', lazy_gettext('Yes')),
                 ('False', lazy_gettext('No'))])
    category_id = SelectField(lazy_gettext('Category'), coerce=int)
    hidden = BooleanField(lazy_gettext('Hide?'))
    password = TextField(lazy_gettext('Password (leave blank for no password)'))
    webhook = TextField(lazy_gettext('Webhook'),
                        [pb_validator.Webhook()])


class TaskPresenterForm(Form):
    id = IntegerField(label=None, widget=HiddenInput())
    editor = TextAreaField('')


class TaskRedundancyForm(Form):
    n_answers = IntegerField(lazy_gettext('Redundancy'),
                             [validators.Required(),
                              validators.NumberRange(
                                  min=1, max=1000,
                                  message=lazy_gettext('Number of answers should be a \
                                                       value between 1 and 1,000'))])


class TaskPriorityForm(Form):
    task_ids = TextField(lazy_gettext('Task IDs'),
                         [validators.Required(),
                          pb_validator.CommaSeparatedIntegers()])

    priority_0 = DecimalField(lazy_gettext('Priority'),
                              [validators.NumberRange(
                                  min=0, max=1,
                                  message=lazy_gettext('Priority should be a \
                                                       value between 0.0 and 1.0'))])


class TaskSchedulerForm(Form):
    _translate_names = lambda variant: (variant[0], lazy_gettext(variant[1]))
    _choices = map(_translate_names, sched_variants())
    sched = SelectField(lazy_gettext('Task Scheduler'), choices=_choices)

    @classmethod
    def update_sched_options(cls, new_options):
        _translate_names = lambda variant: (variant[0], lazy_gettext(variant[1]))
        _choices = map(_translate_names, new_options)
        cls.sched.kwargs['choices'] = _choices


class BlogpostForm(Form):
    id = IntegerField(label=None, widget=HiddenInput())
    title = TextField(lazy_gettext('Title'),
                     [validators.Required(message=lazy_gettext(
                                    "You must enter a title for the post."))])
    body = TextAreaField(lazy_gettext('Body'),
                           [validators.Required(message=lazy_gettext(
                                    "You must enter some text for the post."))])


class PasswordForm(Form):
    password = PasswordField(lazy_gettext('Password'),
                        [validators.Required(message=lazy_gettext(
                                    "You must enter a password"))])


class _BulkTaskCSVImportForm(Form):
    form_name = TextField(label=None, widget=HiddenInput(), default='csv')
    msg_required = lazy_gettext("You must provide a URL")
    msg_url = lazy_gettext("Oops! That's not a valid URL. "
                           "You must provide a valid URL")
    csv_url = TextField(lazy_gettext('URL'),
                        [validators.Required(message=msg_required),
                         validators.URL(message=msg_url)])

    def get_import_data(self):
        return {'type': 'csv', 'csv_url': self.csv_url.data}


class _BulkTaskGDImportForm(Form):
    form_name = TextField(label=None, widget=HiddenInput(), default='gdocs')
    msg_required = lazy_gettext("You must provide a URL")
    msg_url = lazy_gettext("Oops! That's not a valid URL. "
                           "You must provide a valid URL")
    googledocs_url = TextField(lazy_gettext('URL'),
                               [validators.Required(message=msg_required),
                                   validators.URL(message=msg_url)])

    def get_import_data(self):
        return {'type': 'gdocs', 'googledocs_url': self.googledocs_url.data}


class _BulkTaskEpiCollectPlusImportForm(Form):
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


class _BulkTaskFlickrImportForm(Form):
    form_name = TextField(label=None, widget=HiddenInput(), default='flickr')
    msg_required = lazy_gettext("You must provide a valid Flickr album ID")
    album_id = TextField(lazy_gettext('Album ID'),
                         [validators.Required(message=msg_required)])
    def get_import_data(self):
        return {'type': 'flickr', 'album_id': self.album_id.data}


class _BulkTaskDropboxImportForm(Form):
    form_name = TextField(label=None, widget=HiddenInput(), default='dropbox')
    files = FieldList(TextField(label=None, widget=HiddenInput()))
    def get_import_data(self):
        return {'type': 'dropbox', 'files': self.files.data}


class GenericBulkTaskImportForm(object):
    """Callable class that will return, when called, the appropriate form
    instance"""
    _forms = { 'csv': _BulkTaskCSVImportForm,
              'gdocs': _BulkTaskGDImportForm,
              'epicollect': _BulkTaskEpiCollectPlusImportForm,
              'flickr': _BulkTaskFlickrImportForm,
              'dropbox': _BulkTaskDropboxImportForm }

    def __call__(self, form_name, *form_args, **form_kwargs):
        if form_name is None:
            return None
        return self._forms[form_name](*form_args, **form_kwargs)


### Forms for account view

class LoginForm(Form):

    """Login Form class for signin into PyBossa."""

    email = TextField(lazy_gettext('E-mail'),
                      [validators.Required(
                          message=lazy_gettext("The e-mail is required"))])

    password = PasswordField(lazy_gettext('Password'),
                             [validators.Required(
                                 message=lazy_gettext(
                                     "You must provide a password"))])


class RegisterForm(Form):

    """Register Form Class for creating an account in PyBossa."""

    err_msg = lazy_gettext("Full name must be between 3 and %s "
                           "characters long" % USER_FULLNAME_MAX_LENGTH)
    fullname = TextField(lazy_gettext('Full name'),
                         [validators.Length(min=3, max=USER_FULLNAME_MAX_LENGTH, message=err_msg)])

    err_msg = lazy_gettext("User name must be between 3 and %s "
                           "characters long" % USER_NAME_MAX_LENGTH)
    err_msg_2 = lazy_gettext("The user name is already taken")
    name = TextField(lazy_gettext('User name'),
                         [validators.Length(min=3, max=USER_NAME_MAX_LENGTH, message=err_msg),
                          pb_validator.NotAllowedChars(),
                          pb_validator.Unique(user_repo.get_by, 'name', err_msg_2),
                          pb_validator.ReservedName('account', current_app)])

    err_msg = lazy_gettext("Email must be between 3 and %s "
                           "characters long" % EMAIL_MAX_LENGTH)
    err_msg_2 = lazy_gettext("Email is already taken")
    email_addr = EmailField(lazy_gettext('Email Address'),
                           [validators.Length(min=3,
                                              max=EMAIL_MAX_LENGTH,
                                              message=err_msg),
                            validators.Email(),
                            pb_validator.Unique(user_repo.get_by, 'email_addr', err_msg_2)])

    err_msg = lazy_gettext("Password cannot be empty")
    err_msg_2 = lazy_gettext("Passwords must match")
    password = PasswordField(lazy_gettext('New Password'),
                             [validators.Required(err_msg),
                              validators.EqualTo('confirm', err_msg_2)])

    confirm = PasswordField(lazy_gettext('Repeat Password'))


class UpdateProfileForm(Form):

    """Form Class for updating PyBossa's user Profile."""

    id = IntegerField(label=None, widget=HiddenInput())

    err_msg = lazy_gettext("Full name must be between 3 and %s "
                           "characters long" % USER_FULLNAME_MAX_LENGTH)
    fullname = TextField(lazy_gettext('Full name'),
                         [validators.Length(min=3, max=USER_FULLNAME_MAX_LENGTH, message=err_msg)])

    err_msg = lazy_gettext("User name must be between 3 and %s "
                           "characters long" % USER_NAME_MAX_LENGTH)
    err_msg_2 = lazy_gettext("The user name is already taken")
    name = TextField(lazy_gettext('Username'),
                     [validators.Length(min=3, max=USER_NAME_MAX_LENGTH, message=err_msg),
                      pb_validator.NotAllowedChars(),
                      pb_validator.Unique(user_repo.get_by, 'name', err_msg_2),
                      pb_validator.ReservedName('account', current_app)])

    err_msg = lazy_gettext("Email must be between 3 and %s "
                           "characters long" % EMAIL_MAX_LENGTH)
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

    def set_locales(self, locales):
        """Fill the locale.choices."""
        choices = []
        for locale in locales:
            if locale == 'en':
                lang = gettext("English")
            if locale == 'es':
                lang = gettext("Spanish")
            if locale == 'fr':
                lang = gettext("French")
            if locale == 'de':
                lang = gettext("German")
            if locale == 'it':
                lang = gettext("Italian")
            choices.append((locale, lang))
        self.locale.choices = choices


class ChangePasswordForm(Form):

    """Form for changing user's password."""

    current_password = PasswordField(lazy_gettext('Current password'))

    err_msg = lazy_gettext("Password cannot be empty")
    err_msg_2 = lazy_gettext("Passwords must match")
    new_password = PasswordField(lazy_gettext('New password'),
                                 [validators.Required(err_msg),
                                  validators.EqualTo('confirm', err_msg_2)])
    confirm = PasswordField(lazy_gettext('Repeat password'))


class ResetPasswordForm(Form):

    """Class for resetting user's password."""

    err_msg = lazy_gettext("Password cannot be empty")
    err_msg_2 = lazy_gettext("Passwords must match")
    new_password = PasswordField(lazy_gettext('New Password'),
                                 [validators.Required(err_msg),
                                  validators.EqualTo('confirm', err_msg_2)])
    confirm = PasswordField(lazy_gettext('Repeat Password'))



class ForgotPasswordForm(Form):

    """Form Class for forgotten password."""

    err_msg = lazy_gettext("Email must be between 3 and %s "
                           "characters long" % EMAIL_MAX_LENGTH)
    email_addr = EmailField(lazy_gettext('Email Address'),
                           [validators.Length(min=3,
                                              max=EMAIL_MAX_LENGTH,
                                              message=err_msg),
                            validators.Email()])


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
    avatar = FileField(lazy_gettext('Avatar'), validators=[FileRequired()])
    x1 = IntegerField(label=None, widget=HiddenInput(), default=0)
    y1 = IntegerField(label=None, widget=HiddenInput(), default=0)
    x2 = IntegerField(label=None, widget=HiddenInput(), default=0)
    y2 = IntegerField(label=None, widget=HiddenInput(), default=0)
