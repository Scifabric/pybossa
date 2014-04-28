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



class AppFactory(SQLAlchemyModelFactory):
    FACTORY_FOR = App
    FACTORY_SESSION = db.session

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


class BlogpostFactory(SQLAlchemyModelFactory):
    FACTORY_FOR = Blogpost
    FACTORY_SESSION = db.session

    id = factory.Sequence(lambda n: n)
    title = u'Blogpost title'
    body = u'Blogpost body text'
    app = factory.SubFactory('factories.AppFactory')
    app_id = factory.LazyAttribute(lambda blogpost: blogpost.app.id)
    owner = factory.SelfAttribute('app.owner')
    user_id = factory.LazyAttribute(lambda blogpost: blogpost.owner.id)


class CategoryFactory(SQLAlchemyModelFactory):
    FACTORY_FOR = Category
    FACTORY_SESSION = db.session

    id = factory.Sequence(lambda n: n)
    name = factory.Sequence(lambda n: 'category_name_%d' % n)
    short_name = factory.Sequence(lambda n: 'category_short_name_%d' % n)
    description = 'Category description for testing purposes'


class FeaturedFactory(SQLAlchemyModelFactory):
    FACTORY_FOR = Featured
    FACTORY_SESSION = db.session

    id = factory.Sequence(lambda n: n)
    app = factory.SubFactory('factories.AppFactory')
    app_id = factory.LazyAttribute(lambda featured: featured.app.id)


class TaskFactory(SQLAlchemyModelFactory):
    FACTORY_FOR = Task
    FACTORY_SESSION = db.session

    id = factory.Sequence(lambda n: n)
    app = factory.SubFactory('factories.AppFactory')
    app_id = factory.LazyAttribute(lambda task: task.app.id)
    state = u'ongoing'
    quorum = 0
    calibration = 0
    priority_0 = 0
    n_answers = 30


class TaskRunFactory(SQLAlchemyModelFactory):
    FACTORY_FOR = TaskRun
    FACTORY_SESSION = db.session

    id = factory.Sequence(lambda n: n)
    task = factory.SubFactory('factories.TaskFactory')
    task_id = factory.LazyAttribute(lambda task_run: task_run.task.id)
    app = factory.SelfAttribute('task.app')
    app_id = factory.LazyAttribute(lambda task_run: task_run.app.id)
    user = factory.SubFactory('factories.UserFactory')
    user_id = factory.LazyAttribute(lambda task_run: task_run.user.id)
    user_ip = None


class UserFactory(SQLAlchemyModelFactory):
    FACTORY_FOR = User
    FACTORY_SESSION = db.session

    id = factory.Sequence(lambda n: n)
    name = factory.Sequence(lambda n: u'user%d' % n)
    fullname = factory.Sequence(lambda n: u'User %d' % n)
    email_addr = factory.LazyAttribute(lambda usr: u'%s@test.com' % usr.name)
    locale = u'en'
    admin = False
    privacy_mode = True
