import os

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
    username = u'tester'
    api_key = 'tester'
    app_name = u'test-app'

    @classmethod
    def create(cls):
        user = model.User(name=cls.username, api_key=cls.api_key)
        info = {
            'total': 150,
            'long_description': 'hello world'
            }
        app = model.App(
            name=u'My New App',
            short_name=cls.app_name,
            info=info
            )
        app.owner = user
        task_info = {
            'question': 'My random question',
            'url': 'my url'
            }
        task = model.Task(info=task_info)
        task_run_info = {
            'answer': u'annakarenina'
            }
        task_run = model.TaskRun(info=task_run_info)
        task.app = app
        task_run.task = task
        task_run.user = user
        model.Session.add_all([user, app, task, task_run])
        model.Session.commit()
        model.Session.remove()

