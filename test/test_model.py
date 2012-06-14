from base import web, model
import datetime

class TestModel:
    @classmethod
    def setup_class(self):
        model.rebuild_db()

    def test_all(self):
        """Test MODEL works"""
        username = u'test-user-1'
        user = model.User(name=username)
        info = {
            'total': 150,
            'long_description': 'hello world'
            }
        app = model.App(
            name=u'My New App',
            short_name=u'my-new-app',
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
        app_id = app.id 
        user_id = user.id

        model.Session.remove()

        app = model.Session.query(model.App).get(app_id)
        assert app.name == u'My New App', app
        # year would start with 201...
        assert app.created.startswith('201'), app.created
        assert len(app.tasks) == 1, app
        assert app.owner.name == username, app

        out_task = app.tasks[0]
        assert out_task.info['question'] == task_info['question'], out_task
        assert len(out_task.task_runs) == 1, out_task
        outrun = out_task.task_runs[0]
        assert outrun.info['answer'] == task_run_info['answer'], outrun
        assert outrun.user.name == username, outrun

        user = model.User.by_name(username)
        assert user.apps[0].id == app_id, user

    def test_user(self):
        """Test MODEL User works"""
        user = model.User(name=u'test-user', email_addr=u'test@xyz.org')
        model.Session.add(user)
        model.Session.commit()
        user_id = user.id 

        model.Session.remove()
        user = model.User.by_name(u'test-user')
        assert user, user
        assert len(user.api_key) == 36, user

        out = user.dictize()
        assert out['name'] == u'test-user', out

