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



from pybossa.model import db
from pybossa.model.app import App
from pybossa.model.blogpost import Blogpost
from pybossa.model.category import Category
from pybossa.model.featured import Featured
from pybossa.model.task import Task
from pybossa.model.task_run import TaskRun
from pybossa.model.user import User

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


class SQLAlchemyPyBossaFactory(SQLAlchemyModelFactory):
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


class AppFactory(SQLAlchemyPyBossaFactory):
    FACTORY_FOR = App

    id = factory.Sequence(lambda n: n)
    name = factory.Sequence(lambda n: u'My App number %d' % n)
    short_name = factory.Sequence(lambda n: u'app%d' % n)
    description = u'App description'
    allow_anonymous_contributors = True
    long_tasks = 0
    hidden = 0
    owner = factory.SubFactory('factories.UserFactory')
    owner_id = factory.LazyAttribute(lambda app: app.owner.id)
    category = factory.SubFactory('factories.CategoryFactory')
    category_id = factory.LazyAttribute(lambda app: app.category.id)


class BlogpostFactory(SQLAlchemyPyBossaFactory):
    FACTORY_FOR = Blogpost

    id = factory.Sequence(lambda n: n)
    title = u'Blogpost title'
    body = u'Blogpost body text'
    app = factory.SubFactory('factories.AppFactory')
    app_id = factory.LazyAttribute(lambda blogpost: blogpost.app.id)
    owner = factory.SelfAttribute('app.owner')
    user_id = factory.LazyAttribute(lambda blogpost: blogpost.owner.id)


class CategoryFactory(SQLAlchemyPyBossaFactory):
    FACTORY_FOR = Category

    id = factory.Sequence(lambda n: n)
    name = factory.Sequence(lambda n: 'category_name_%d' % n)
    short_name = factory.Sequence(lambda n: 'category_short_name_%d' % n)
    description = 'Category description for testing purposes'


class FeaturedFactory(SQLAlchemyPyBossaFactory):
    FACTORY_FOR = Featured

    id = factory.Sequence(lambda n: n)
    app = factory.SubFactory('factories.AppFactory')
    app_id = factory.LazyAttribute(lambda featured: featured.app.id)


class TaskFactory(SQLAlchemyPyBossaFactory):
    FACTORY_FOR = Task

    id = factory.Sequence(lambda n: n)
    app = factory.SubFactory('factories.AppFactory')
    app_id = factory.LazyAttribute(lambda task: task.app.id)
    state = u'ongoing'
    quorum = 0
    calibration = 0
    priority_0 = 0.0
    n_answers = 30


class TaskRunFactory(SQLAlchemyPyBossaFactory):
    FACTORY_FOR = TaskRun

    id = factory.Sequence(lambda n: n)
    task = factory.SubFactory('factories.TaskFactory')
    task_id = factory.LazyAttribute(lambda task_run: task_run.task.id)
    app = factory.SelfAttribute('task.app')
    app_id = factory.LazyAttribute(lambda task_run: task_run.app.id)
    user = factory.SubFactory('factories.UserFactory')
    user_id = factory.LazyAttribute(lambda task_run: task_run.user.id)
    user_ip = None


class UserFactory(SQLAlchemyPyBossaFactory):
    FACTORY_FOR = User

    id = factory.Sequence(lambda n: n)
    name = factory.Sequence(lambda n: u'user%d' % n)
    fullname = factory.Sequence(lambda n: u'User %d' % n)
    email_addr = factory.LazyAttribute(lambda usr: u'%s@test.com' % usr.name)
    locale = u'en'
    admin = False
    privacy_mode = True
    api_key =  factory.Sequence(lambda n: u'api-key%d' % n)
