from base import model, db


class TestModel:
    @classmethod
    def setup_class(self):
        model.rebuild_db()

    def tearDown(self):
        db.session.remove()

    def test_all(self):
        """Test MODEL works"""
        username = u'test-user-1'
        user = model.User(name=username)
        info = {
            'total': 150,
            'long_description': 'hello world'}
        app = model.App(
            name=u'My New App',
            short_name=u'my-new-app',
            info=info)
        app.owner = user
        task_info = {
            'question': 'My random question',
            'url': 'my url'}
        task = model.Task(info=task_info)
        task_run_info = {'answer': u'annakarenina'}
        task_run = model.TaskRun(info=task_run_info)
        task.app = app
        task_run.task = task
        task_run.user = user
        db.session.add_all([user, app, task, task_run])
        db.session.commit()
        app_id = app.id

        db.session.remove()

        app = db.session.query(model.App).get(app_id)
        assert app.name == u'My New App', app
        # year would start with 201...
        assert app.created.startswith('201'), app.created
        assert app.long_tasks == 0, app.long_tasks
        assert app.hidden == 0, app.hidden
        assert app.time_estimate == 0, app
        assert app.time_limit == 0, app
        assert app.calibration_frac == 0, app
        assert app.bolt_course_id == 0
        assert len(app.tasks) == 1, app
        assert app.owner.name == username, app
        out_task = app.tasks[0]
        assert out_task.info['question'] == task_info['question'], out_task
        assert out_task.quorum == 0, out_task
        assert out_task.state == "ongoing", out_task
        assert out_task.calibration == 0, out_task
        assert out_task.priority_0 == 0, out_task
        assert len(out_task.task_runs) == 1, out_task
        outrun = out_task.task_runs[0]
        assert outrun.info['answer'] == task_run_info['answer'], outrun
        assert outrun.user.name == username, outrun

        user = model.User.by_name(username)
        assert user.apps[0].id == app_id, user

    def test_user(self):
        """Test MODEL User works"""
        user = model.User(name=u'test-user', email_addr=u'test@xyz.org')
        db.session.add(user)
        db.session.commit()

        db.session.remove()
        user = model.User.by_name(u'test-user')
        assert user, user
        assert len(user.api_key) == 36, user

        out = user.dictize()
        assert out['name'] == u'test-user', out
