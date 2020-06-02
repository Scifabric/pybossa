# -*- coding: utf8 -*-
# This file is part of PyBossa.
#
# Copyright (C) 2020 SciFabric LTD.
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
from wtforms import SelectField
from wtforms.widgets import Select, html_params, HTMLString

class SelectProps(Select):
    def __call__(self, field, **kwargs):
        kwargs.setdefault('id', field.id)
        if self.multiple:
            kwargs['multiple'] = True
        html = ['<select %s>' % html_params(name=field.name, **kwargs)]
        for val, label, selected, props in field.iter_choices():
            html.append(self.render_option(val, label, selected, **props))
        html.append('</select>')
        return HTMLString(''.join(html))

class SelectFieldWithProps(SelectField):
    widget = SelectProps()

    def iter_choices(self):
        for value, label, render_args in self.choices:
            yield (value, label, self.coerce(value) == self.data, render_args)

    def pre_validate(self, form):
         if self.choices:
             for v, _, _ in self.choices:
                 if self.data == v:
                     break
             else:
                 raise ValueError(self.gettext('is not a valid choice'))