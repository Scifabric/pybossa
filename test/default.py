from pybossa.model import db, rebuild_db
from pybossa.core import create_app, sentinel
from pybossa.model.app import App
from pybossa.model.category import Category
from pybossa.model.task import Task
from pybossa.model.task_run import TaskRun
from pybossa.model.user import User
from functools import wraps
import random

flask_app = create_app()

def with_context(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        print "calling Decorated function"
        with flask_app.app_context():
            return f(*args, **kwargs)
    return decorated_function


class Test(object):
    def setUp(self):
        self.flask_app = flask_app
        self.app = flask_app.test_client()
        with self.flask_app.app_context():
            rebuild_db()

    def tearDown(self):
        with self.flask_app.app_context():
            db.session.remove()
            self.redis_flushall()

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

    def create(self,sched='default'):
        root, user,user2 = self.create_users()
        info = {
            'total': 150,
            'long_description': 'hello world',
            'task_presenter': 'TaskPresenter',
            'sched': sched
            }

        app = self.create_app(info)
        app.owner = user

        db.session.add(root)
        db.session.commit()
        db.session.add(user)
        db.session.commit()
        db.session.add(user2)
        db.session.commit()
        db.session.add(app)


        task_info = {
            'question': 'My random question',
            'url': 'my url'
            }
        task_run_info = {
            'answer': u'annakarenina'
            }

        # Create the task and taskruns for the first app
        for i in range (0,10):
             task, task_run = self.create_task_and_run(task_info, task_run_info, app, user,i)
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

        app = self.create_app(info)
        app.owner = user

        db.session.add_all([root, user, user2, app])

        task_info = {
            'question': 'My random question',
            'url': 'my url'
            }
        task_run_info = {
            'answer': u'annakarenina'
            }

        # Create the task and taskruns for the first app
        task, task_run = self.create_task_and_run(task_info, task_run_info, app, user,1)
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

    def create_app(self,info):
        with self.flask_app.app_context():
            category = db.session.query(Category).first()
            if category is None:
                self._create_categories()
                category = db.session.query(Category).first()
            app = App(
                    name=self.app_name,
                    short_name=self.app_short_name,
                    description=u'description',
                    hidden=0,
                    category_id=category.id,
                    info=info
                )
            return app

    def create_task_and_run(self,task_info, task_run_info, app, user, order):
        task = Task(app_id = 1, state = '0', info = task_info, n_answers=10)
        task.app = app
        # Taskruns will be assigned randomly to a signed user or an anonymous one
        if random.randint(0,1) == 1:
            task_run = TaskRun(
                    app_id = 1,
                    task_id = 1,
                    user_id = 1,
                    info = task_run_info)
            task_run.user = user
        else:
            task_run = TaskRun(
                    app_id = 1,
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
        sentinel.connection.master_for('mymaster').flushall()

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
    def create_app(cls,info):
        category = db.session.query(Category).first()
        if category is None:
            cls.create_categories()
            category = db.session.query(Category).first()
        app = App(
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
        task = Task(app_id = 1, state = '0', info = task_info, n_answers=10)
        task.app = app
        # Taskruns will be assigned randomly to a signed user or an anonymous one
        if random.randint(0,1) == 1:
            task_run = TaskRun(
                    app_id = 1,
                    task_id = 1,
                    user_id = 1,
                    info = task_run_info)
            task_run.user = user
        else:
            task_run = TaskRun(
                    app_id = 1,
                    task_id = 1,
                    user_ip = '127.0.0.%s' % order,
                    info = task_run_info)
        task_run.task = task
        return task, task_run

    @classmethod
    def create_categories(cls):
        names = [cls.cat_1, cls.cat_2]
        db.session.add_all([Category(name=c_name,
                                           short_name=c_name.lower().replace(" ",""),
                                           description=c_name)
                            for c_name in names])
        db.session.commit()

    @classmethod
    def redis_flushall(cls):
        sentinel.connection.master_for('mymaster').flushall()

def assert_not_raises(exception, call, *args, **kwargs):
    try:
        call(*args, **kwargs)
        assert True
    except exception as ex:
        assert False, str(ex)
