import json

from base import Fixtures
from helper import web as web_helper
from pybossa.hateoas import Hateoas


class TestHateoas(web_helper.Helper):
    url = "/app/%s/tasks/export" % Fixtures.app_short_name

    hateoas = Hateoas()

    def setUp(self):
        super(TestHateoas, self).setUp()
        Fixtures.create()

    # Tests

    def test_00_link_object(self):
        """Test HATEOAS object link is created"""
        # For app
        res = self.app.get("/api/app/1", follow_redirects=True)
        output = json.loads(res.data)
        err_msg = "There should be a Link with the object URI"
        assert output['link'] is not None, err_msg
        app_link = self.hateoas.link(rel='self', title='app',
                                     href='http://localhost/api/app/1')

        err_msg = "The object link is wrong: %s" % output['link']
        assert app_link == output['link'], err_msg
        err_msg = "There should not be links, this is the parent object"
        assert output.get('links') is None, err_msg

        # For task
        res = self.app.get("/api/task/1", follow_redirects=True)
        output = json.loads(res.data)
        err_msg = "There should be a Link with the object URI"
        assert output['link'] is not None, err_msg
        task_link = self.hateoas.link(rel='self', title='task',
                                      href='http://localhost/api/task/1')
        err_msg = "The object link is wrong: %s" % output['link']
        assert task_link == output['link'], err_msg
        err_msg = "There should be one parent link: app"
        assert output.get('links') is not None, err_msg
        assert len(output.get('links')) == 1, err_msg
        err_msg = "The parent link is wrong"
        app_link = self.hateoas.link(rel='parent', title='app',
                                     href='http://localhost/api/app/1')
        assert output.get('links')[0] == app_link, err_msg

        # For taskrun
        res = self.app.get("/api/taskrun/1", follow_redirects=True)
        output = json.loads(res.data)
        err_msg = "There should be a Link with the object URI"
        assert output['link'] is not None, err_msg
        task_link = self.hateoas.link(rel='self', title='taskrun',
                                      href='http://localhost/api/taskrun/1')
        err_msg = "The object link is wrong: %s" % output['link']
        assert task_link == output['link'], err_msg
        err_msg = "There should be two parent links: app and task"
        assert output.get('links') is not None, err_msg
        assert len(output.get('links')) == 2, err_msg
        err_msg = "The parent app link is wrong"
        app_link = self.hateoas.link(rel='parent', title='app',
                                     href='http://localhost/api/app/1')
        assert output.get('links')[0] == app_link, err_msg

        err_msg = "The parent task link is wrong"
        app_link = self.hateoas.link(rel='parent', title='task',
                                     href='http://localhost/api/task/1')
        assert output.get('links')[1] == app_link, err_msg
