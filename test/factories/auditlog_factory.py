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

from pybossa.model.auditlog import Auditlog
from . import BaseFactory, factory, auditlog_repo


class AuditlogFactory(BaseFactory):
    class Meta:
        model = Auditlog

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        log = model_class(*args, **kwargs)
        auditlog_repo.save(log)
        return log

    id = factory.Sequence(lambda n: n)
    app_id = 1
    app_short_name = 'app'
    user_id = 1
    user_name = 'example user'
    action = 'update'
    caller = 'web'
    attribute = 'attribute'
    old_value ='old'
    new_value = 'new'
