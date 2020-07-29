from mock import patch

from default import db, with_context
from factories import ProjectFactory, UserFactory
from helper import web
from pybossa.repositories import ProjectRepository, UserRepository

project_repo = ProjectRepository(db)
user_repo = UserRepository(db)


class TestProjectExtConfig(web.Helper):

    @with_context
    def setUp(self):
        super(TestProjectExtConfig, self).setUp()
        self.owner = UserFactory.create(email_addr='a@a.com')
        self.owner.set_password('1234')
        user_repo.save(self.owner)
        project = ProjectFactory.create(owner=self.owner, published=False)
        self.project_id = project.id
        self.signin(email='a@a.com', password='1234')

    @with_context
    def test_no_config(self):
        project = project_repo.get(self.project_id)
        res = self.app.get('/project/%s/ext-config' % project.short_name)

        assert 'No external services have been configured' in res.data

    @with_context
    def test_form_display(self):
        ext_config = {
            'ml_service': {
                'display': 'Active Learning Config',
                'fields': {
                    'model': ('TextField', 'Model', None)
                }
            }
        }
        with patch.dict(self.flask_app.config, {'EXTERNAL_CONFIGURATIONS': ext_config}):
            project = project_repo.get(self.project_id)
            res = self.app.get('/project/%s/ext-config' % project.short_name)

        assert 'Active Learning Config' in res.data
        assert 'Model' in res.data

    @with_context
    def test_add_config(self):
        ext_config = {
            'ml_service': {
                'display': 'Active Learning Config',
                'fields': {
                    'model': ('TextField', 'Model', None)
                }
            }
        }
        with patch.dict(self.flask_app.config, {'EXTERNAL_CONFIGURATIONS': ext_config}):
            project = project_repo.get(self.project_id)
            data = {
                'ml_service': True,
                'model': 'random_forest'
            }
            self.app.post('/project/%s/ext-config' % project.short_name, data=data)

        project = project_repo.get(self.project_id)
        assert project.info['ext_config']['ml_service']['model'] == 'random_forest'
        
    @with_context
    def test_update_config(self):
        ext_config = {
                'ml_service': {
                    'display': 'Active Learning Config',
                    'fields': {
                        'model': ('TextField', '', None)
                    }
                }
            }

        with patch.dict(self.flask_app.config, 
                        {'EXTERNAL_CONFIGURATIONS': ext_config}):
            project = project_repo.get(self.project_id)
            self.app.post('/project/%s/ext-config' % project.short_name)

        project = project_repo.get(self.project_id)
        assert 'TextField' not in project.info['ext_config'].keys()
