import os
import random

import pybossa.web as web
import pybossa.model as model

_here = os.path.dirname(__file__)
web.app.config['TESTING'] = True
dburi = 'sqlite:///%s/test.db' % _here
print dburi
web.app.config['SQLALCHEMY_DATABASE_URI'] = dburi
engine = model.create_engine(dburi)
model.set_engine(engine)

class Fixtures:
    fullname = u'T Tester'
    fullname2 = u'T Tester 2'
    email_addr = u'tester@tester.com'
    email_addr2 = u'tester-2@tester.com'
    name = u'tester'
    name2 = u'tester-2'
    api_key = 'tester'
    api_key_2 = 'tester-2'
    app_name = u'test-app'

    @classmethod
    def create(cls):
        user = model.User(
                email_addr = cls.email_addr, 
                name = cls.name, 
                fullname = cls.fullname, 
                api_key = cls.api_key)

        user2 = model.User(
                email_addr = cls.email_addr2, 
                name = cls.name2, 
                fullname = cls.fullname2, 
                api_key=cls.api_key_2)

        info = {
            'total': 150,
            'long_description': 'hello world'
            }

        app = model.App(
                name = u'My New App',
                short_name = cls.app_name,
                description = u'description',
                hidden = 0,
                info = info
            )

        app.owner = user
        task_info = {
            'question': 'My random question',
            'url': 'my url'
            }
        task_run_info = {
            'answer': u'annakarenina'
            }

        model.Session.add_all([user, user2, app])

        # Create the task and taskruns for the first app
        for i in range (0,10):
            task = model.Task(app_id = 1, state = '0', info = task_info)
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
                        user_ip = '127.0.0.1', 
                        info = task_run_info)
            task_run.task = task
            model.Session.add_all([task, task_run])
        model.Session.commit()
        model.Session.remove()
