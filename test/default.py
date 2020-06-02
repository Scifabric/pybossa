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
import json
from sqlalchemy import text
from pybossa.core import db
from pybossa.core import create_app, sentinel, signer
from pybossa.cookies import CookieHandler
from pybossa.model.project import Project
from pybossa.model.category import Category
from pybossa.model.task import Task
from pybossa.model.task_run import TaskRun
from pybossa.model.user import User
from pybossa.leaderboard.jobs import leaderboard
import pybossa.model as model
from functools import wraps
from factories import reset_all_pk_sequences
import random
from mock import MagicMock


flask_app = create_app(run_as_server=False)


def with_context(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        with flask_app.app_context():
            return f(*args, **kwargs)
    return decorated_function


def with_context_settings(**kwargs):
    def decorator(f):
        @wraps(f)
        def decorated(*fargs, **fkwargs):
            config = flask_app.config
            original = {key: config.get(key) for key in kwargs}
            config.update(kwargs)
            with flask_app.app_context():
                try:
                    return f(*fargs, **fkwargs)
                finally:
                    config.update(original)
        return decorated
    return decorator


def delete_indexes():
    sql = text('''select * from pg_indexes WHERE schemaname = current_schema() and tablename = 'users_rank' ''')
    results = db.session.execute(sql)
    for row in results:
        sql = 'drop index %s;' % row.indexname
        db.session.execute(sql)
        db.session.commit()

def delete_materialized_views():
    """Delete materialized views."""
    sql = text('''SELECT relname
               FROM pg_class WHERE relname LIKE '%dashboard%';''')
    results = db.session.execute(sql)
    for row in results:
        sql = 'drop materialized view if exists "%s" cascade' % row.relname
        db.session.execute(sql)
        db.session.commit()
    sql = text('''SELECT relname
               FROM pg_class WHERE relname LIKE '%users_rank%';''')
    results = db.session.execute(sql)
    for row in results:
        if "_idx" not in row.relname:
            sql = 'drop materialized view if exists "%s" cascade' % row.relname
            db.session.execute(sql)
            db.session.commit()


def rebuild_db():
    """Rebuild the DB."""
    delete_indexes()
    delete_materialized_views()
    db.drop_all()
    db.create_all()


class Test(object):
    def setUp(self):
        self.flask_app = flask_app
        self.app = flask_app.test_client()
        with self.flask_app.app_context():
            rebuild_db()
            reset_all_pk_sequences()
            leaderboard()

    def app_get_json(self, url, follow_redirects=False, headers=None):
        return self.app.get(url, follow_redirects=follow_redirects,
                            headers=headers, content_type='application/json')

    def app_post_json(self, url, data=None, follow_redirects=False, headers=None):
        if data:
            return self.app.post(url, data=json.dumps(data),
                                 follow_redirects=follow_redirects,
                                 headers=headers, content_type='application/json')
        else:
            return self.app.post(url,
                                 follow_redirects=follow_redirects,
                                 headers=headers, content_type='application/json')

    def tearDown(self):
        with self.flask_app.app_context():
            delete_indexes()
            delete_materialized_views()
            db.session.remove()
            self.redis_flushall()
            reset_all_pk_sequences()

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
    project_name = u'My New Project'
    project_short_name = u'test-app'
    password = u'tester'
    root_password = password + 'root'
    cat_1 = 'thinking'
    cat_2 = 'sensing'

    def create(self,sched='default', input_data_class='L4 - public', output_data_class='L4 - public'):
        root, user,user2 = self.create_users()
        info = {
            'total': 150,
            'long_description': 'hello world',
            'task_presenter': 'TaskPresenter',
            'sched': sched,
            'data_classification': {
                'input_data': input_data_class,
                'output_data': output_data_class
            }
        }

        project = self.create_project(info)
        project.owner = user

        db.session.add(root)
        db.session.commit()
        db.session.add(user)
        db.session.commit()
        db.session.add(user2)
        db.session.commit()
        project.owners_ids = [user.id]
        db.session.add(project)


        task_info = {
            'question': 'My random question',
            'url': 'my url'
            }
        task_run_info = {
            'answer': u'annakarenina'
            }

        # Create the task and taskruns for the first project
        for i in range (0,10):
             task, task_run = self.create_task_and_run(task_info, task_run_info, project, user,i)
             db.session.add_all([task, task_run])
        db.session.commit()
        db.session.remove()

    def create_2(self,sched='default'):
        root, user,user2 = self.create_users()

        info = {
            'total': 150,
            'long_description': 'hello world',
            'task_presenter': 'TaskPresenter',
            'sched': sched
            }

        project = self.create_project(info)
        project.owner = user

        db.session.add_all([root, user, user2, project])

        task_info = {
            'question': 'My random question',
            'url': 'my url'
            }
        task_run_info = {
            'answer': u'annakarenina'
            }

        # Create the task and taskruns for the first project
        task, task_run = self.create_task_and_run(task_info, task_run_info, project, user,1)
        db.session.add_all([task, task_run])

        db.session.commit()
        db.session.remove()


    def create_users(self):
        root = User(
                email_addr = self.root_addr,
                name = self.root_name,
                passwd_hash = self.root_password,
                fullname = self.fullname,
                api_key = self.root_api_key)
        root.set_password(self.root_password)

        user = User(
                email_addr = self.email_addr,
                name = self.name,
                passwd_hash = self.password,
                fullname = self.fullname,
                api_key = self.api_key
                )

        user.set_password(self.password)

        user2 = User(
                email_addr = self.email_addr2,
                name = self.name2,
                passwd_hash = self.password + "2",
                fullname = self.fullname2,
                api_key=self.api_key_2)

        user2.set_password(self.password)

        return root, user, user2

    def create_project(self,info):
        with self.flask_app.app_context():
            category = db.session.query(Category).first()
            if category is None:
                self._create_categories()
                category = db.session.query(Category).first()
            project = Project(
                    name=self.project_name,
                    short_name=self.project_short_name,
                    description=u'description',
                    category_id=category.id,
                    published=True,
                    info=info
                )
            return project

    def create_task_and_run(self,task_info, task_run_info, project, user, order):
        task = Task(project_id = 1, state = '0', info = task_info, n_answers=10)
        task.project = project
        # Taskruns will be assigned randomly to a signed user or an anonymous one
        if random.randint(0,1) == 1:
            task_run = TaskRun(
                    project_id = 1,
                    task_id = 1,
                    user_id = 1,
                    info = task_run_info)
            task_run.user = user
        else:
            task_run = TaskRun(
                    project_id = 1,
                    task_id = 1,
                    user_ip = '127.0.0.%s' % order,
                    info = task_run_info)
        task_run.task = task
        return task, task_run

    def _create_categories(self):
        names = [self.cat_1, self.cat_2]
        db.session.add_all([Category(name=c_name,
                                           short_name=c_name.lower().replace(" ",""),
                                           description=c_name)
                            for c_name in names])
        db.session.commit()

    def redis_flushall(self):
        sentinel.master.flushall()

    def set_proj_passwd_cookie(self, project, user=None, username=None):
        from pybossa.core import user_repo
        if username:
            user = user_repo.get_by_name(username)
        cookie = signer.dumps([get_user_id_or_ip(user)])
        self.app.set_cookie('/', '%spswd' % project.short_name, cookie)

    def get_csrf(self, endpoint):
        """Return csrf token for endpoint."""
        res = self.app.get(endpoint,
                           content_type='application/json')
        csrf = json.loads(res.data).get('form').get('csrf')
        return csrf

def get_user_id_or_ip(user):
    if not user:
        return dict(user_id=None, user_ip='127.0.0.1', external_uid=None)
    return dict(user_id=user.id, user_ip=None, external_uid=None)


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
    project_name = u'My New Project'
    project_short_name = u'test-app'
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

        project = Fixtures.create_project(info)
        project.owner = user

        db.session.add(root)
        db.session.commit()
        db.session.add(user)
        db.session.commit()
        db.session.add(user2)
        db.session.commit()
        project.owners_ids = [user.id]
        db.session.add(project)


        task_info = {
            'question': 'My random question',
            'url': 'my url'
            }
        task_run_info = {
            'answer': u'annakarenina'
            }

        # Create the task and taskruns for the first project
        for i in range (0,10):
             task, task_run = Fixtures.create_task_and_run(task_info, task_run_info, project, user,i)
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

        project = Fixtures.create_project(info)
        project.owner = user

        db.session.add_all([root, user, user2, project])

        task_info = {
            'question': 'My random question',
            'url': 'my url'
            }
        task_run_info = {
            'answer': u'annakarenina'
            }

        # Create the task and taskruns for the first project
        task, task_run = Fixtures.create_task_and_run(task_info, task_run_info, project, user,1)
        db.session.add_all([task, task_run])

        db.session.commit()
        db.session.remove()


    @classmethod
    def create_users(cls):
        root = User(
                email_addr = cls.root_addr,
                name = cls.root_name,
                passwd_hash = cls.root_password,
                fullname = cls.fullname,
                api_key = cls.root_api_key)
        root.set_password(cls.root_password)

        user = User(
                email_addr = cls.email_addr,
                name = cls.name,
                passwd_hash = cls.password,
                fullname = cls.fullname,
                api_key = cls.api_key)

        user.set_password(cls.password)

        user2 = User(
                email_addr = cls.email_addr2,
                name = cls.name2,
                passwd_hash = cls.password + "2",
                fullname = cls.fullname2,
                api_key=cls.api_key_2)

        user2.set_password(cls.password)

        return root, user, user2

    @classmethod
    def create_project(cls,info):
        category = db.session.query(Category).first()
        if category is None:
            cls.create_categories()
            category = db.session.query(Category).first()
        project = Project(
                name=cls.project_name,
                short_name=cls.project_short_name,
                description=u'description',
                category_id=category.id,
                published=True,
                info=info
            )
        return project

    @classmethod
    def create_task_and_run(cls,task_info, task_run_info, project, user, order):
        task = Task(project_id = 1, state = '0', info = task_info, n_answers=10)
        task.project = project
        # Taskruns will be assigned randomly to a signed user or an anonymous one
        if random.randint(0,1) == 1:
            task_run = TaskRun(
                    project_id = 1,
                    task_id = 1,
                    user_id = 1,
                    info = task_run_info)
            task_run.user = user
        else:
            task_run = TaskRun(
                    project_id = 1,
                    task_id = 1,
                    user_ip = '127.0.0.%s' % order,
                    info = task_run_info)
        task_run.task = task
        return task, task_run

    @classmethod
    def create_categories(cls):
        names = [cls.cat_1, cls.cat_2]
        db.session.add_all([Category(name=c_name,
                                     short_name=c_name.lower().replace(" ", ""),
                                     description=c_name)
                            for c_name in names])
        db.session.commit()

    @classmethod
    def redis_flushall(cls):
        sentinel.master.flushall()

def assert_not_raises(exception, call, *args, **kwargs):
    try:
        call(*args, **kwargs)
        assert True
    except exception as ex:
        assert False, str(ex)


class FakeResponse(object):
    def __init__(self, **kwargs):
        self.__dict__.update(**kwargs)


def mock_contributions_guard(stamped=True, timestamp='2015-11-18T16:29:25.496327'):
    fake_guard_instance = MagicMock()
    fake_guard_instance.check_task_stamped.return_value = stamped
    fake_guard_instance.retrieve_timestamp.return_value = timestamp
    return fake_guard_instance


def mock_contributions_guard_presented_time(stamped=True, timestamp='2015-11-18T16:29:25.496327'):
    fake_guard_instance = MagicMock()
    fake_guard_instance.check_task_presented_timestamp.return_value = stamped
    fake_guard_instance.retrieve_presented_timestamp.return_value = timestamp
    return fake_guard_instance
