from helper import web
from default import db, with_context
from factories import ProjectFactory, UserFactory, TaskFactory, TaskRunFactory
from pybossa.repositories import UserRepository, ProjectRepository
from mock import patch

project_repo = ProjectRepository(db)
from pybossa.core import user_repo

class TestProjectReport(web.Helper):

    @with_context
    def test_nonadmin_noncoowner_access_project_report_results_403(self):
        """Test nonadmin noncoowner accessing project report returns 403"""
        self.register()
        user = user_repo.get(1)
        project = ProjectFactory.create(owner=user)
        self.signout()
        self.register(fullname='Juan', name='juan', password='juana')
        self.signin(email="juan@example.com", password='juana')
        url = '/project/%s/projectreport/export' % project.short_name
        res = self.app.get(url, follow_redirects=True)
        assert res.status_code == 403, res.data

    @with_context
    def test_admin_owner_can_access_project_report(self):
        """Test admin can access project report"""
        self.register()
        user = user_repo.get(1)
        project = ProjectFactory.create(owner=user)
        url = '/project/%s/projectreport/export' % project.short_name
        res = self.app.get(url, follow_redirects=True)
        assert res.status_code == 200, res.data

    @with_context
    def test_project_report_with_bad_params_results_404(self):
        """Test project report accessed with incorrect params returns 404"""
        self.register()
        user = user_repo.get(1)
        project = ProjectFactory.create(owner=user)
        url = '/project/%s/projectreport/export?badparam=badval' % project.short_name
        res = self.app.get(url, follow_redirects=True)
        assert res.status_code == 404, res.data

    @with_context
    def test_project_report_with_bad_type_results_404(self):
        """Test project report accessed with bad type returns 404"""
        self.register()
        user = user_repo.get(1)
        project = ProjectFactory.create(owner=user)
        url = '/project/%s/projectreport/export?type=badtype&format=csv' % project.short_name
        res = self.app.get(url, follow_redirects=True)
        assert res.status_code == 404, res.data

    @with_context
    def test_project_report_with_bad_format_results_415(self):
        """Test project report accessed with bad format returns 415"""
        self.register()
        user = user_repo.get(1)
        project = ProjectFactory.create(owner=user)
        url = '/project/%s/projectreport/export?type=project&format=badfmt' % project.short_name
        res = self.app.get(url, follow_redirects=True)
        assert res.status_code == 415, res.data

    @with_context
    def test_admin_owner_can_access_project_report_with_params(self):
        """Test project report works when accessed with correct params"""
        self.register()
        user = user_repo.get(1)
        project = ProjectFactory.create(owner=user)
        url = '/project/%s/projectreport/export?type=project&format=csv' % project.short_name
        res = self.app.get(url, follow_redirects=True)
        assert res.status_code == 200, res.status_code

    @with_context
    def test_project_report_with_task_details(self):
        """Test project report works with project details"""
        admin = UserFactory.create(admin=True)
        admin.set_password('1234')
        user_repo.save(admin)

        owner = UserFactory.create(pro=False)
        project = ProjectFactory.create(owner=owner)
        task = TaskFactory.create(project=project)
        TaskRunFactory.create(task=task)
        url = '/project/%s/projectreport/export?type=project&format=csv' % project.short_name
        res = self.app_get_json(url, follow_redirects=True)
        print(res)

    @with_context
    @patch('pybossa.exporter.csv_reports_export.uploader.file_exists', return_value=True)
    def test_project_report_delete_existing_report(self, mock_zip_exists):
        """Test project report is generated with deleting existing report zip"""
        self.register()
        user = user_repo.get(1)
        project = ProjectFactory.create(owner=user)
        url = '/project/%s/projectreport/export?type=project&format=csv' % project.short_name
        res = self.app.get(url, follow_redirects=True)

    @with_context
    @patch('pybossa.exporter.csv_reports_export.isinstance', return_value=False)
    def test_project_report_no_zip_without_uploader(self, mock_no_up):
        """Test project report does not returns zip with no uploader instance """
        self.register()
        user = user_repo.get(1)
        project = ProjectFactory.create(owner=user)
        url = '/project/%s/projectreport/export?type=project&format=csv' % project.short_name
        res = self.app.get(url, follow_redirects=True)
        assert res.status_code == 500, res.data
