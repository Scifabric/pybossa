import json
from mock import patch
from collections import namedtuple
from bs4 import BeautifulSoup

from base import web, db, model, Fixtures
from helper import web as web_helper
from pybossa.ckan import Ckan


FakeRequest = namedtuple('FakeRequest', ['text', 'status_code', 'headers'])


class TestCkanWeb(web_helper.Helper):
    url = "/app/%s/tasks/export" % Fixtures.app_short_name

    def setUp(self):
        super(TestCkanWeb, self).setUp()
        Fixtures.create()

    # Tests

    def test_00_anonymous(self):
        """Test CKAN anonymous cannot export data via CKAN"""
        res = self.app.get(self.url, follow_redirects=True)
        dom = BeautifulSoup(res.data)
        err_msg = "The CKAN exporter should not be available for anon users"
        assert dom.find(id="ckan") is None, err_msg

    def test_01_authenticated(self):
        """Test CKAN authenticated app owners can export data via CKAN"""
        res = self.signin(email=Fixtures.email_addr, password=Fixtures.password)
        res = self.app.get(self.url, follow_redirects=True)
        dom = BeautifulSoup(res.data)
        err_msg = "The CKAN exporter should be available for the owner of the app"
        assert dom.find(id="ckan") is not None, err_msg

        self.signout()

        self.signin(email=Fixtures.email_addr2, password=Fixtures.password)
        res = self.app.get(self.url, follow_redirects=True)
        dom = BeautifulSoup(res.data)
        err_msg = "The CKAN exporter should be ONLY available for the owner of the app"
        assert dom.find(id="ckan") is None, err_msg

    def test_02_export_links(self):
        """Test CKAN export links task and task run are available"""
        self.signin(email=Fixtures.email_addr, password=Fixtures.password)
        res = self.app.get(self.url, follow_redirects=True)
        dom = BeautifulSoup(res.data)
        err_msg = "There should be a warning about adding a CKAN api Key"
        assert dom.find(id="ckan_warning") is not None, err_msg
        # Add a CKAN API key to the user
        u = db.session.query(model.User).filter_by(name=Fixtures.name).first()
        u.ckan_api = "ckan-api-key"
        db.session.add(u)
        db.session.commit()
        # Request again the page
        res = self.app.get(self.url, follow_redirects=True)
        err_msg = "There should be two buttons to export Task and Task Runs"
        dom = BeautifulSoup(res.data)
        assert dom.find(id="ckan_task") is not None, err_msg
        assert dom.find(id="ckan_task_run") is not None, err_msg


class TestCkanModule(object):

    ckan = Ckan(url="http://datahub.io", api_key="fake-api-key")
    task_resource_id = "0dde48c7-a0e9-445f-bc84-6365ec057450"
    task_run_resource_id = "a49448dc-228a-4d54-a697-ba02c50e0143"
    package_id = "4bcf844c-3ad0-4203-8418-32e7d7c4ce96"
    pkg_json_not_found = {
        "help": "Return ...",
        "success": False,
        "error": {
            "message": "Not found",
            "__type": "Not Found Error"}}

    pkg_json_found = {
        "help": "Return the metadata of a dataset ...",
        "success": True,
        "result": {
            "license_title": "",
            "maintainer": "",
            "relationships_as_object": [],
            "maintainer_email": "",
            "revision_timestamp": "2013-04-11T11:45:52.689160",
            "id": package_id,
            "metadata_created": "2013-04-11T11:39:56.003541",
            "metadata_modified": "2013-04-12T10:50:45.132825",
            "author": "Daniel Lombrana Gonzalez",
            "author_email": "",
            "state": "deleted",
            "version": "",
            "license_id": "",
            "type": None,
            "resources": [
                {
                    "resource_group_id": "f45c29ce-97f3-4b1f-b060-3306ffedb64b",
                    "cache_last_updated": None,
                    "revision_timestamp": "2013-04-12T10:50:41.635556",
                    "webstore_last_updated": None,
                    "id": task_resource_id,
                    "size": None,
                    "state": "active",
                    "last_modified": None,
                    "hash": "",
                    "description": "tasks",
                    "format": "",
                    "tracking_summary": {
                        "total": 0,
                        "recent": 0
                    },
                    "mimetype_inner": None,
                    "mimetype": None,
                    "cache_url": None,
                    "name": "task",
                    "created": "2013-04-12T05:50:41.776512",
                    "url": "http://localhost:5000/app/urbanpark/",
                    "webstore_url": None,
                    "position": 0,
                    "revision_id": "85027e11-fcbd-4362-9298-9755c99729b0",
                    "resource_type": None
                },
                {
                    "resource_group_id": "f45c29ce-97f3-4b1f-b060-3306ffedb64b",
                    "cache_last_updated": None,
                    "revision_timestamp": "2013-04-12T10:50:45.132825",
                    "webstore_last_updated": None,
                    "id": task_run_resource_id,
                    "size": None,
                    "state": "active",
                    "last_modified": None,
                    "hash": "",
                    "description": "task_runs",
                    "format": "",
                    "tracking_summary": {
                        "total": 0,
                        "recent": 0
                    },
                    "mimetype_inner": None,
                    "mimetype": None,
                    "cache_url": None,
                    "name": "task_run",
                    "created": "2013-04-12T05:50:45.193953",
                    "url": "http://localhost:5000/app/urbanpark/",
                    "webstore_url": None,
                    "position": 1,
                    "revision_id": "a1c52da7-5f2a-4bd4-8e58-b58e3caa11b5",
                    "resource_type": None
                }
            ],
            "tags": [],
            "tracking_summary": {
                "total": 0,
                "recent": 0
            },
            "groups": [],
            "relationships_as_subject": [],
            "name": "urbanpark",
            "isopen": False,
            "url": "http://localhost:5000/app/urbanpark/",
            "notes": "",
            "title": "Urban Parks",
            "extras": [],
            "revision_id": "b74c202a-1ad6-42a9-a878-012827d86c54"
        }
    }

    task_datastore = {
        u'help': u'Adds a ...',
        u'success': True,
        u'result': {
            u'fields': [{u'type': u'json', u'id': u'info'},
                        {u'type': u'int', u'id': u'user_id'},
                        {u'type': u'int', u'id': u'task_id'},
                        {u'type': u'timestamp', u'id': u'created'},
                        {u'type': u'timestamp', u'id': u'finish_time'},
                        {u'type': u'int', u'id': u'calibration'},
                        {u'type': u'int', u'id': u'app_id'},
                        {u'type': u'text', u'id': u'user_ip'},
                        {u'type': u'int', u'id': u'TaskRun_task'},
                        {u'type': u'int', u'id': u'TaskRun_user'},
                        {u'type': u'int', u'id': u'timeout'},
                        {u'type': u'int', u'id': u'id'}],
            u'method': u'insert',
            u'indexes': u'id',
            u'primary_key': u'id',
            u'resource_id': task_resource_id}}

    task_upsert = {"help": "Updates",
                   "success": True,
                   "result": {
                       "records": [
                           {"info": {"foo": "bar"},
                            "n_answers": 1000,
                            "quorum": 0,
                            "created": "2012-07-29T17:12:10.519270",
                            "calibration": 0,
                            "app_id": 120,
                            "state": "0",
                            "id": 6345,
                            "priority_0": 0.0}],
                       "method": "insert",
                       "resource_id": task_resource_id}}

    server_error = FakeRequest("Server Error", 500, {'content-type': 'text/html'})

    def setUp(self):
        self.app = web.app
        model.rebuild_db()
        Fixtures.create()

    def tearDown(self):
        db.session.remove()

    @classmethod
    def teardown_class(cls):
        model.rebuild_db()

    # Tests

    @patch('pybossa.ckan.requests.get')
    def test_00_package_exists_returns_false(self, Mock):
        """Test CKAN get_resource_id works"""
        html_request = FakeRequest(json.dumps(self.pkg_json_not_found), 200,
                                   {'content-type': 'application/json'})
        Mock.return_value = html_request
        with self.app.test_request_context('/'):
            # Resource that exists
            out, e = self.ckan.package_exists(name='not-found')
            assert out is False, "It should return False as pkg does not exist"
            # Handle error in CKAN server
            Mock.return_value = self.server_error
            try:
                pkg, e = self.ckan.package_exists(name="something-goes-wrong")
                if e:
                    raise e
            except Exception as out:
                type, msg, status_code = out.args
                assert "Server Error" in msg, msg
                assert status_code == 500, "status_code should be 500"
                assert type == "CKAN: the remote site failed! package_show failed"
            # Now with a broken JSON item
            Mock.return_value = FakeRequest("simpletext", 200,
                                            {'content-type': 'text/html'})
            out, e = self.ckan.package_exists(name='not-found')
            assert out is False, "It should return False as pkg does not exist"
            # Handle error in CKAN server
            try:
                pkg, e = self.ckan.package_exists(name="something-goes-wrong")
                if e:
                    raise e
            except Exception as out:
                type, msg, status_code = out.args
                assert status_code == 200, "status_code should be 200"
                assert type == "CKAN: JSON not valid"

    @patch('pybossa.ckan.requests.get')
    def test_01_package_exists_returns_pkg(self, Mock):
        """Test CKAN get_resource_id works"""
        html_request = FakeRequest(json.dumps(self.pkg_json_found), 200,
                                   {'content-type': 'application/json'})
        Mock.return_value = html_request
        with self.app.test_request_context('/'):
            # Resource that exists
            out, e = self.ckan.package_exists(name='urbanpark')
            assert out is not False, "It should return a pkg"
            err_msg = "The pkg id should be the same"
            assert out['id'] == self.pkg_json_found['result']['id'], err_msg

    @patch('pybossa.ckan.requests.get')
    def test_02_get_resource_id(self, Mock):
        """Test CKAN get_resource_id works"""
        html_request = FakeRequest(json.dumps(self.pkg_json_found), 200,
                                   {'content-type': 'application/json'})
        Mock.return_value = html_request
        with self.app.test_request_context('/'):
            # Resource that exists
            # Get the package
            out, e = self.ckan.package_exists(name='urbanpark')
            # Get the resource id for Task
            out = self.ckan.get_resource_id(name='task')
            err_msg = "It should return the task resource ID"
            assert out == self.task_resource_id, err_msg
            # Get the resource id for TaskRun
            out = self.ckan.get_resource_id(name='task_run')
            err_msg = "It should return the task_run resource ID"
            assert out == self.task_run_resource_id, err_msg
            # Get the resource id for a non existant resource
            err_msg = "It should return false"
            out = self.ckan.get_resource_id(name='non-existant')
            assert out is False, err_msg

    @patch('pybossa.ckan.requests.post')
    def test_03_package_create(self, Mock):
        """Test CKAN package_create works"""
        # It should return self.pkg_json_found with an empty Resources list
        html_request = FakeRequest(json.dumps(self.pkg_json_found), 200,
                                   {'content-type': 'application/json'})
        Mock.return_value = html_request
        with self.app.test_request_context('/'):
            # Resource that exists
            app = model.App(short_name='urbanpark', name='Urban Parks')
            user = model.User(fullname='Daniel Lombrana Gonzalez')
            out = self.ckan.package_create(app=app, user=user, url="http://something.com")
            err_msg = "The package ID should be the same"
            assert out['id'] == self.package_id, err_msg

            # Check the exception
            Mock.return_value = self.server_error
            try:
                self.ckan.package_create(app=app, user=user, url="http://something.com")
            except Exception as out:
                type, msg, status_code = out.args
                assert "Server Error" in msg, msg
                assert 500 == status_code, status_code
                assert "CKAN: the remote site failed! package_create failed" == type, type

    @patch('pybossa.ckan.requests.post')
    def test_05_resource_create(self, Mock):
        """Test CKAN resource_create works"""
        pkg_request = FakeRequest(json.dumps(self.pkg_json_found), 200,
                                  {'content-type': 'application/json'})

        rsrc_request = FakeRequest(json.dumps(
            self.pkg_json_found['result']['resources'][0]),
            200,
            {'content-type': 'text/html'})
        Mock.return_value = pkg_request
        with self.app.test_request_context('/'):
            # Resource that exists
            app = model.App(short_name='urbanpark', name='Urban Parks')
            user = model.User(fullname='Daniel Lombrana Gonzalez')
            self.ckan.package_create(app=app, user=user, url="http://something.com")
            Mock.return_value = rsrc_request
            out = self.ckan.resource_create(name='task')
            err_msg = "It should create the task resource"
            assert out["id"] == self.task_resource_id, err_msg
            Mock.return_value = self.server_error
            try:
                self.ckan.resource_create(name='something-goes-wrong')
            except Exception as out:
                type, msg, status_code = out.args
                assert "Server Error" in msg, msg
                assert 500 == status_code, status_code
                assert "CKAN: the remote site failed! resource_create failed" == type, type

    @patch('pybossa.ckan.requests.post')
    def test_05_datastore_create(self, Mock):
        """Test CKAN datastore_create works"""
        html_request = FakeRequest(json.dumps(self.task_datastore), 200,
                                   {'content-type': 'application/json'})

        Mock.return_value = html_request
        with self.app.test_request_context('/'):
            out = self.ckan.datastore_create(name='task',
                                             resource_id=self.task_resource_id)
            err_msg = "It should ref the task resource ID"
            assert out['resource_id'] == self.task_resource_id, err_msg
            # Check the error
            Mock.return_value = self.server_error
            try:
                self.ckan.datastore_create(name='task',
                                           resource_id=self.task_resource_id)
            except Exception as out:
                type, msg, status_code = out.args
                assert "Server Error" in msg, err_msg
                assert 500 == status_code, status_code
                assert "CKAN: the remote site failed! datastore_create failed" == type, type

    @patch('pybossa.ckan.requests.post')
    def test_06_datastore_upsert(self, Mock):
        """Test CKAN datastore_upsert works"""
        html_request = FakeRequest(json.dumps(self.task_upsert), 200,
                                   {'content-type': 'application/json'})

        record = dict(info=dict(foo="bar"))
        Mock.return_value = html_request
        with self.app.test_request_context('/'):
            out = self.ckan.datastore_upsert(name='task',
                                             records=json.dumps([record]),
                                             resource_id=self.task_resource_id)
            err_msg = "It should return True"
            assert out is True, err_msg
            # Check the error
            Mock.return_value = self.server_error
            try:
                self.ckan.datastore_upsert(name='task',
                                           records=json.dumps([record]),
                                           resource_id=self.task_resource_id)
            except Exception as out:
                type, msg, status_code = out.args
                assert "Server Error" in msg, msg
                assert 500 == status_code, status_code
                assert "CKAN: the remote site failed! datastore_upsert failed" == type, type

    @patch('pybossa.ckan.requests.post')
    def test_07_datastore_delete(self, Mock):
        """Test CKAN datastore_delete works"""
        html_request = FakeRequest(json.dumps({}), 200,
                                   {'content-type': 'application/json'})

        Mock.return_value = html_request
        with self.app.test_request_context('/'):
            out = self.ckan.datastore_delete(name='task',
                                             resource_id=self.task_resource_id)
            err_msg = "It should return True"
            assert out is True, err_msg
            # Check the error
            Mock.return_value = self.server_error
            try:
                self.ckan.datastore_delete(name='task',
                                           resource_id=self.task_resource_id)
            except Exception as out:
                type, msg, status_code = out.args
                assert "Server Error" in msg, msg
                assert 500 == status_code, status_code
                assert "CKAN: the remote site failed! datastore_delete failed" == type, type

    @patch('pybossa.ckan.requests.post')
    def test_08_package_update(self, Mock):
        """Test CKAN package_update works"""
        html_request = FakeRequest(json.dumps(self.pkg_json_found), 200,
                                   {'content-type': 'application/json'})
        Mock.return_value = html_request
        with self.app.test_request_context('/'):
            # Resource that exists
            app = model.App(short_name='urbanpark', name='Urban Parks')
            user = model.User(fullname='Daniel Lombrana Gonzalez')
            out = self.ckan.package_update(app=app, user=user,
                                           url="http://something.com",
                                           resources=self.pkg_json_found['result']['resources'])
            err_msg = "The package ID should be the same"
            assert out['id'] == self.package_id, err_msg

            # Check the exception
            Mock.return_value = self.server_error
            try:
                self.ckan.package_update(app=app, user=user,
                                         url="http://something.com",
                                         resources=self.pkg_json_found['result']['resources'])
            except Exception as out:
                type, msg, status_code = out.args
                assert "Server Error" in msg, msg
                assert 500 == status_code, status_code
                assert "CKAN: the remote site failed! package_update failed" == type, type
