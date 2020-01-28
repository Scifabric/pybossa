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

from datetime import date
from flask_babel import lazy_gettext
from wtforms.validators import ValidationError
import re
import requests

from pybossa.util import is_reserved_name, check_password_strength
from pybossa.data_access import valid_user_type_based_data_access


class Unique(object):
    """Validator that checks field uniqueness."""

    def __init__(self, query_function, field_name, message=None):
        self.query_function = query_function
        self.field_name = field_name
        if not message:  # pragma: no cover
            message = lazy_gettext(u'This item already exists')
        self.message = message

    def __call__(self, form, form_field):
        field_value = form_field.data
        if isinstance(field_value, basestring):
            field_value = form_field.data.strip()
        filters = {self.field_name: field_value}
        check = self.query_function(**filters)
        if 'id' in form:
            if check:
                id = type(check.id)(form.id.data)
            else:
                id = int(form.id.data)
        else:
            id = None
        if check and (id is None or id != check.id):
            raise ValidationError(self.message)


class UniqueCaseInsensitive(Unique):

    def __init__(self, query_function, field_name, message=None):
        super(UniqueCaseInsensitive, self).__init__(
            query_function=query_function,
            field_name=field_name,
            message=message)

    def __call__(self, form, form_field):
        if not isinstance(form_field.data, basestring):
            return False
        form_field.data = form_field.data.strip().lower()
        super(UniqueCaseInsensitive, self).__call__(form, form_field)


class NotAllowedChars(object):
    """Validator that checks field not allowed chars"""
    not_valid_chars = '$#&\/| \t'

    def __init__(self, message=None):
        if not message:
            self.message = lazy_gettext(u'%s and whitespace symbols are forbidden'
                                        % self.not_valid_chars.strip())
        else:  # pragma: no cover
            self.message = message

    def __call__(self, form, field):
        if field.data:
            if any(c in field.data for c in self.not_valid_chars):
                raise ValidationError(self.message)


class CommaSeparatedIntegers(object):
    """Validator that validates input fields that have comma separated values"""
    not_valid_chars = '$#&\/| '

    def __init__(self, message=None):
        if not message:
            self.message = lazy_gettext(
                u'Only comma separated values are allowed, no spaces')

        else:  # pragma: no cover
            self.message = message

    def __call__(self, form, field):
        pattern = re.compile('^[\d,]+$')
        if pattern.match(field.data) is None:
            raise ValidationError(self.message)


class Webhook(object):
    """Validator for webhook URLs"""

    def __init__(self, message=None):
        if not message:
            self.message = lazy_gettext(u'Invalid URL')

        else:  # pragma: no cover
            self.message = message

    def __call__(self, form, field):
        try:
            if field.data:
                r = requests.get(field.data)
                if r.status_code != 200:
                    raise ValidationError(self.message)
        except requests.exceptions.ConnectionError:
            raise ValidationError(lazy_gettext(u"Connection error"))


class ReservedName(object):
    """Validator to avoid URL conflicts when creating/modifying projects or
    user accounts"""

    def __init__(self, blueprint, message=None):
        self.blueprint = blueprint
        if not message:  # pragma: no cover
            message = lazy_gettext(u'This name is used by the system.')
        self.message = message

    def __call__(self, form, field):
        if is_reserved_name(self.blueprint, field.data):
            raise ValidationError(self.message)

class CheckPasswordStrength(object):
    """ Validator to apply strong password policy """

    def __init__(
            self, message=None, min_len=8,
            max_len=None, uppercase=True,
            lowercase=True, numeric=True,
            special=True):
        self.min_len = min_len
        self.max_len = max_len
        self.uppercase = uppercase
        self.lowercase = lowercase
        self.numeric = numeric
        self.special = special

        if message:
            self.message = message
        else:
            self.message = self._get_message(
                                    uppercase, lowercase,
                                    numeric, special)

    def __call__(self, form, field):
        pwd = field.data
        valid, message = check_password_strength(
                            pwd, self.min_len, self.max_len,
                            self.uppercase, self.lowercase,
                            self.numeric, self.special, self.message)
        if not valid:
            raise ValidationError(message)

    def _get_message(self, uppercase=True, lowercase=True,
                     numeric=True, special=True):
        message = []
        if uppercase:
            message.append('one uppercase')
        if lowercase:
            message.append('one lowercase')
        if numeric:
            message.append('one numeric ')
        if special:
            message.append('one special !@$%^&*#')

        if message:
            return 'Password must contain at least {} character.'\
                .format(', '.join(message))
        return None


class TimeFieldsValidator(object):
    def __init__(self, fields, message=None):
        if not message:
            message = "Fill out empty field(s)"
        self.message = message
        self.fields = fields

    def __call__(self, form, field):
        values = [form.data[fld] for fld in self.fields]
        values.append(field.data)
        if any(values) and not all(values):
            raise ValidationError(self.message)

class UserTypeValiadator(object):
    def __init__(self, message=None):
        if not message:
            message = message = lazy_gettext(u'Invalid data access')
        self.message = message

    def __call__(self, form, field):
        user_type = form.user_type.data
        access_levels = field.data
        valid, valid_data_access = valid_user_type_based_data_access(user_type, access_levels)
        if not valid:
            self.message = lazy_gettext(u'Invalid data access {}. Valid data access(s) for user type {} are {}'
                .format(','.join(access_levels), user_type, ', '.join(valid_data_access)))
            raise ValidationError(self.message)

class EndDateValidator(object):
    """Ensure end date is not less than start date."""
    def __init__(self, message=None):
        if not message:
            message = lazy_gettext("Start date must be earlier than end date.")
        self.message = message

    def __call__(self, form, field):
        if not (form.start_date.data and form.end_date.data):
            return

        if form.start_date.data > form.end_date.data:
            raise ValidationError(self.message)

class NotInFutureValidator(object):
    """Ensures that a date is not in the future."""
    def __init__(self, message="Date cannot be greater than today's date."):
        self.message = lazy_gettext(message)

    def __call__(self, form, field):
        if field.data > date.today():
            raise ValidationError(self.message)
