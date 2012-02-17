import json

from base import web, model, Fixtures
from nose.tools import assert_equal


class TestAPI:
    def setUp(self):
        self.app = web.app.test_client()
        model.rebuild_db()
        Fixtures.create()

    @classmethod
    def teardown_class(cls):
        model.rebuild_db()

    def test_01_app_query(self):
        res = self.app.get('/api/app')
        data = json.loads(res.data)
        assert len(data) == 1, data
        app = data[0]
        assert app['info']['total'] == 150, data

    def test_02_app_post(self):
        name = u'XXXX Project'
        data = dict(
            name=name,
            short_name='xxxx-project'
            )
        data = json.dumps(data)
        # no api-key
        res = self.app.post('/api/app',
            data=data
        )
        assert res.status == '403 FORBIDDEN', res.status
        # now a real user
        res = self.app.post('/api/app?api_key=' + Fixtures.api_key,
            data=data,
        )
        out = model.Session.query(model.App).filter_by(name=name).one()
        assert out
        assert out.short_name == 'xxxx-project', out
        id_ = out.id
        model.Session.remove()

        # test update
        data = {
            'name': 'My New Title'
            }
        datajson = json.dumps(data)
        res = self.app.put('/api/app/%s' % id_,
            data=data
        )
        assert res.status == '403 FORBIDDEN', res.status
        print data
        res = self.app.put('/api/app/%s?api_key=%s' % (id_, Fixtures.api_key),
            data=datajson
        )
        assert res.status == '200 OK', res.data
        out2 = model.Session.query(model.App).get(id_)
        assert_equal(out2.name, data['name'])

    def _test_03_app_task_post(self):
        data = dict(
            app_id=out.id,
            state=1,
            info='my task data'
            )
        data = json.dumps(data)
        res = self.app.post('/api/task',
            data=data
        )
        tasks = model.Session.query(model.Task).filter_by(app_id=out.id).all()
        assert tasks, tasks

        data = dict(
            app_id=out.id,
            task_id=tasks[0].id,
            info='my task result'
            )
        data = json.dumps(data)
        res = self.app.post('/api/taskrun',
            data=data
        )
        taskrun = model.Session.query(model.TaskRun).filter_by(app_id=out.id).all()
        assert taskrun, taskrun
        assert taskrun[0].created, taskrun
        assert taskrun[0].app_id == out.id


