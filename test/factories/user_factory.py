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

from pybossa.model.user import User
from . import BaseFactory, factory, user_repo


class UserFactory(BaseFactory):
    class Meta:
        model = User

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        user = model_class(*args, **kwargs)
        user_repo.save(user)
        return user

    @classmethod
    def _setup_next_sequence(cls):
        return 1

    id = factory.Sequence(lambda n: n)
    name = factory.Sequence(lambda n: u'user%d' % n)
    fullname = factory.Sequence(lambda n: u'User %d' % n)
    email_addr = factory.LazyAttribute(lambda usr: u'%s@test.com' % usr.name)
    locale = u'en'
    admin = False
    privacy_mode = True
    api_key =  factory.Sequence(lambda n: u'api-key%d' % n)
