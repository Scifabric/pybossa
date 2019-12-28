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

    id = factory.Sequence(lambda n: n)
    name = factory.Sequence(lambda n: 'user%d' % n)
    fullname = factory.Sequence(lambda n: 'User %d' % n)
    email_addr = factory.LazyAttribute(lambda usr: '%s@test.com' % usr.name)
    locale = 'en'
    admin = False
    pro = False
    ldap = None
    subscribed = True
    privacy_mode = True
    restrict = False
    consent = False
    api_key = factory.Sequence(lambda n: 'api-key%d' % n)
    info = dict(foo='bar', container='container',
                avatar='img.png',
                avatar_url='http://cdn.com/container/img.png')
