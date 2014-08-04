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

from flask_wtf import Form
from flask_wtf.file import FileField, FileRequired
from wtforms import IntegerField, DecimalField, TextField, BooleanField, \
    SelectField, validators, TextAreaField, PasswordField
from wtforms.widgets import HiddenInput
from flask.ext.babel import lazy_gettext, gettext
from pybossa.core import db
import pybossa.validator as pb_validator
from pybossa import model

class AvatarUploadForm(Form):
    id = IntegerField(label=None, widget=HiddenInput())
    avatar = FileField(lazy_gettext('Avatar'), validators=[FileRequired()])
    x1 = IntegerField(label=None, widget=HiddenInput(), default=0)
    y1 = IntegerField(label=None, widget=HiddenInput(), default=0)
    x2 = IntegerField(label=None, widget=HiddenInput(), default=0)
    y2 = IntegerField(label=None, widget=HiddenInput(), default=0)


class AppForm(Form):
    name = TextField(lazy_gettext('Name'),
                     [validators.Required(),
                      pb_validator.Unique(db.session, model.app.App, model.app.App.name,
                                          message=lazy_gettext("Name is already taken."))])
    short_name = TextField(lazy_gettext('Short Name'),
                           [validators.Required(),
                            pb_validator.NotAllowedChars(),
                            pb_validator.Unique(
                                db.session, model.app.App, model.app.App.short_name,
                                message=lazy_gettext(
                                    "Short Name is already taken."))])
    long_description = TextAreaField(lazy_gettext('Long Description'),
                                     [validators.Required()])


class AppUpdateForm(AppForm):
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
    sched = SelectField(lazy_gettext('Task Scheduler'),
                        choices=[('default', lazy_gettext('Default')),
                                 ('breadth_first', lazy_gettext('Breadth First')),
                                 ('depth_first', lazy_gettext('Depth First')),
                                 ('random', lazy_gettext('Random'))])


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