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

from pybossa.core import db

import factory
from factory.alchemy import SQLAlchemyModelFactory


def reset_all_pk_sequences():
    AppFactory.reset_sequence()
    BlogpostFactory.reset_sequence()
    CategoryFactory.reset_sequence()
    FeaturedFactory.reset_sequence()
    TaskFactory.reset_sequence()
    TaskRunFactory.reset_sequence()
    UserFactory.reset_sequence()


class BaseFactory(SQLAlchemyModelFactory):
    FACTORY_SESSION = db.session

    @classmethod
    def _create(cls, target_class, *args, **kwargs):
        """The default beahaviour is to simply add the object to the SQLAlchemy
        session. Here, we also flush it as autoflush is disabled in the
        flask-SQLAlchemy extension"""
        session = cls.FACTORY_SESSION
        obj = target_class(*args, **kwargs)
        session.add(obj)
        session.commit()
        return obj


# Import the factories
from app_factory import AppFactory
from blogpost_factory import BlogpostFactory
from category_factory import CategoryFactory
from featured_factory import FeaturedFactory
from task_factory import TaskFactory
from taskrun_factory import TaskRunFactory, AnonymousTaskRunFactory
from user_factory import UserFactory
