import json

from base import web, model


class TestAPI:
    def setUp(self):
        self.app = web.app.test_client()
        model.rebuild_db()

    def test_01(self):
        res = self.app.get('/api/app')
        # assert 'nothing' in res.data, res.data

    def test_02(self):
        name = u'XXXX Project'
        data = dict(
            name=name,
            short_name='xxxx-project'
            )
        data = json.dumps(data)
        res = self.app.post('/api/app',
            data=data
        )
        out = model.Session.query(model.App).filter_by(name=name).one()
        assert out

        data = dict(
            app_id=out.id,
            state=1,
            info='my job data'
            )
        data = json.dumps(data)
        res = self.app.post('/api/task',
            data=data
        )
        tasks = model.Session.query(model.Task).filter_by(app_id=out.id).all()
        assert tasks, tasks

        data = dict(
            app_id=out.id,
            job_id=tasks[0].id,
            info='my job result'
            )
        data = json.dumps(data)
        res = self.app.post('/api/taskrun',
            data=data
        )
        taskrun = model.Session.query(model.TaskRun).filter_by(app_id=out.id).all()
        assert taskrun, taskrun
        assert taskrun[0].create_time, taskrun
        assert taskrun[0].app_id == out.id


