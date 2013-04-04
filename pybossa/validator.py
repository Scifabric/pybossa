# This file is part of PyBOSSA.
#
# PyBOSSA is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# PyBOSSA is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with PyBOSSA.  If not, see <http://www.gnu.org/licenses/>.

from flaskext.babel import lazy_gettext
from flaskext.wtf import ValidationError


class Unique(object):
    """Validator that checks field uniqueness"""
    def __init__(self, session, model, field, message=None):
        self.session = session
        self.model = model
        self.field = field
        if not message:
            message = lazy_gettext(u'This item already exists')
        self.message = message

    def __call__(self, form, field):
        check = self.session.query(self.model)\
                    .filter(self.field == field.data)\
                    .first()
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
        else:
            self.message = message

    def __call__(self, form, field):
        if any(c in field.data for c in self.not_valid_chars):
            raise ValidationError(self.message)
