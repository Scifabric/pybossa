# -*- coding: utf8 -*-
# This file is part of PyBossa.
#
# Copyright (C) 2013 SF Isle of Man Limited
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

from flask.ext.babel import lazy_gettext
from wtforms.validators import ValidationError
import re


class Unique(object):

    """Validator that checks field uniqueness."""

    def __init__(self, query_function, field_name, message=None):
        self.query_function = query_function
        self.field_name = field_name
        if not message:  # pragma: no cover
            message = lazy_gettext(u'This item already exists')
        self.message = message

    def __call__(self, form, form_field):
        filters = {self.field_name: form_field.data}
        check = self.query_function(**filters)
        if 'id' in form:
            id = form.id.data
        else:
            id = None
        if check and (id is None or id != check.id):
            raise ValidationError(self.message)


class NotAllowedChars(object):
    """Validator that checks field not allowed chars"""
    not_valid_chars = '$#&\/| '

    def __init__(self, message=None):
        if not message:
            self.message = lazy_gettext(u'%sand space symbols are forbidden'
                                        % self.not_valid_chars)
        else:  # pragma: no cover
            self.message = message

    def __call__(self, form, field):
        if any(c in field.data for c in self.not_valid_chars):
            raise ValidationError(self.message)


class CommaSeparatedIntegers(object):
    """Validator that validates input fields that have comma separated values"""
    not_valid_chars = '$#&\/| '

    def __init__(self, message=None):
        if not message:
            self.message = lazy_gettext(u'Only comma separated values are allowed, no spaces')

        else:  # pragma: no cover
            self.message = message

    def __call__(self, form, field):
        pattern = re.compile('^[\d,]+$')
        if pattern.match(field.data) is None:
            raise ValidationError(self.message)
