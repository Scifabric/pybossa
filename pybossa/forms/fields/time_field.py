# -*- coding: utf8 -*-
# This file is part of PyBossa.
#
# Copyright (C) 2018 SciFabric LTD.
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



from __future__ import absolute_import

import datetime
import time

from wtforms.fields import Field

from wtforms_components.widgets import TimeInput

class TimeField(Field):
    widget = TimeInput()
    error_msg = 'Please fill out field'

    def __init__(self, label=None, validators=None, format="%H:%M", **kwargs):
        super(TimeField, self).__init__(label, validators, **kwargs)
        self.format = format

    def _value(self):
        if self.raw_data:
            return ' '.join(self.raw_data)
        elif self.data is not None:
            return self.data
        else:
            return ''

    def process_formdata(self, valuelist):
        if valuelist:
            time_str = ' '.join(valuelist)
            try:
                self.data = datetime.time(*time.strptime(time_str, self.format)[3:6])
                self.data = self.data.strftime("%H:%M")

            except ValueError:
                self.data = None
