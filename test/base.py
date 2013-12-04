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

import os
import random

import pybossa.web as web
import pybossa.model as model
from pybossa.core import db, mail, app, redis_master

_here = os.path.dirname(__file__)
web.app.config['TESTING'] = True
web.app.config['CSRF_ENABLED'] = False
web.app.config['SQLALCHEMY_DATABASE_URI'] = web.app.config['SQLALCHEMY_DATABASE_TEST_URI']
web.app.config['CSRF_ENABLED'] = False
web.app.config['MAIL_SERVER'] = 'localhost'
web.app.config['MAIL_USERNAME'] = None
web.app.config['MAIL_PASSWORD'] = None
web.app.config['MAIL_PORT'] = 25
web.app.config['MAIL_FAIL_SILENTLY'] = False
web.app.config['MAIL_DEFAULT_SENDER'] = 'PyBossa Support <info@pybossa.com>'

web.app.config['ANNOUNCEMENT'] = {'admin': 'Root Message',
                                  'user': 'User Message',
                                  'owner': 'Owner Message'}

web.app.config['CKAN_URL'] = 'http://datahub.io'
web.app.config['CKAN_NAME'] = 'CKAN server'
web.app.config['ENFORCE_PRIVACY'] = False
#cache.init_app(web.app)
mail.init_app(web.app)
#engine = model.create_engine(web.app.config['SQLALCHEMY_DATABASE_URI'])
#model.set_engine(engine)

def redis_flushall():
    redis_master.flushall()

class Fixtures:
    fullname = u'T Tester'
    fullname2 = u'T Tester 2'
    email_addr = u'tester@tester.com'
    email_addr2 = u'tester-2@tester.com'
    root_addr = u'root@root.com'
    name = u'tester'
    name2 = u'tester-2'
    root_name = u'root'
    api_key = 'tester'
    api_key_2 = 'tester-2'
    root_api_key = 'root'
    app_name = u'My New App'
    app_short_name = u'test-app'
    password = u'tester'
    root_password = password + 'root'
    cat_1 = 'thinking'
    cat_2 = 'sensing'

    @classmethod
    def create(cls,sched='default'):
        root, user,user2 = Fixtures.create_users()
        info = {
            'total': 150,
            'long_description': 'hello world',
            'task_presenter': 'TaskPresenter',
            'sched': sched
            }

        app = Fixtures.create_app(info)
        app.owner = user

        db.session.add(root)
        db.session.commit()
        db.session.add(user)
        db.session.commit()
        db.session.add(user2)
        db.session.commit()
        db.session.add(app)


        task_info = {
            'n_answers': 10,
            'question': 'My random question',
            'url': 'my url'
            }
        task_run_info = {
            'answer': u'annakarenina'
            }

        # Create the task and taskruns for the first app
        for i in range (0,10):
             task, task_run = Fixtures.create_task_and_run(task_info, task_run_info, app, user,i)
             db.session.add_all([task, task_run])
        db.session.commit()
        db.session.remove()

    @classmethod
    def create_2(cls,sched='default'):
        root, user,user2 = Fixtures.create_users()

        info = {
            'total': 150,
            'long_description': 'hello world',
            'task_presenter': 'TaskPresenter',
            'sched': sched
            }

        app = Fixtures.create_app(info)
        app.owner = user

        db.session.add_all([root, user, user2, app])

        task_info = {
            'n_answers': 10,
            'question': 'My random question',
            'url': 'my url'
            }
        task_run_info = {
            'answer': u'annakarenina'
            }

        # Create the task and taskruns for the first app
        task, task_run = Fixtures.create_task_and_run(task_info, task_run_info, app, user,1)
        db.session.add_all([task, task_run])

        db.session.commit()
        db.session.remove()


    @classmethod
    def create_users(cls):
        root = model.User(
                email_addr = cls.root_addr,
                name = cls.root_name,
                passwd_hash = cls.root_password,
                fullname = cls.fullname,
                api_key = cls.root_api_key)
        root.set_password(cls.root_password)

        user = model.User(
                email_addr = cls.email_addr,
                name = cls.name,
                passwd_hash = cls.password,
                fullname = cls.fullname,
                api_key = cls.api_key)

        user.set_password(cls.password)

        user2 = model.User(
                email_addr = cls.email_addr2,
                name = cls.name2,
                passwd_hash = cls.password + "2",
                fullname = cls.fullname2,
                api_key=cls.api_key_2)

        user2.set_password(cls.password)

        return root, user, user2

    @classmethod
    def create_app(cls,info):
        category = db.session.query(model.Category).first()
        if category is None:
            cls.create_categories()
            category = db.session.query(model.Category).first()
        app = model.App(
                name=cls.app_name,
                short_name=cls.app_short_name,
                description=u'description',
                hidden=0,
                category_id=category.id,
                info=info
            )
        return app

    @classmethod
    def create_task_and_run(cls,task_info, task_run_info, app, user, order):
        task = model.Task(app_id = 1, state = '0', info = task_info, n_answers=10)
        task.app = app
        # Taskruns will be assigned randomly to a signed user or an anonymous one
        if random.randint(0,1) == 1:
            task_run = model.TaskRun(
                    app_id = 1,
                    task_id = 1,
                    user_id = 1,
                    info = task_run_info)
            task_run.user = user
        else:
            task_run = model.TaskRun(
                    app_id = 1,
                    task_id = 1,
                    user_ip = '127.0.0.%s' % order,
                    info = task_run_info)
        task_run.task = task
        return task, task_run

    @classmethod
    def create_categories(cls):
        names = [cls.cat_1, cls.cat_2]
        db.session.add_all([model.Category(name=c_name,
                                           short_name=c_name.lower().replace(" ",""),
                                           description=c_name)
                            for c_name in names])
        db.session.commit()
