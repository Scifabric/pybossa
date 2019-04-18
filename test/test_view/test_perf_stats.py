import json
from mock import patch

from default import db, with_context
from factories import ProjectFactory, UserFactory, TaskRunFactory
from helper import web
from pybossa.repositories import ProjectRepository, UserRepository

project_repo = ProjectRepository(db)
user_repo = UserRepository(db)


class TestPerfStats(web.Helper):

    @with_context
    def test_owner_has_access(self):
        project = ProjectFactory.create(published=True)
        url = '/project/%s/performancestats?api_key=%s' % (project.short_name, project.owner.api_key)
        res = self.app.get(url)
        assert 'Performance Statistics' in res.data, res.data

    @with_context
    def test_not_owner_has_not_access(self):
        owner, user = UserFactory.create_batch(2)
        project = ProjectFactory.create(owner=owner, published=True)
        url = '/project/%s/performancestats?api_key=%s' % (project.short_name, user.api_key)
        res = self.app.get(url)
        assert 'You do not have the permission to access the requested resource.' in res.data, res.data

    @with_context
    def test_has_fields_config(self):
        fields = {'hello': {}}
        project = ProjectFactory.create(published=True, info={'answer_fields': fields})
        url = '/project/%s/performancestats?api_key=%s' % (project.short_name, project.owner.api_key)
        res = self.app_get_json(url)

        data = json.loads(res.data)
        assert data['answer_fields'] == fields, data

    @with_context
    def test_has_users(self):
        users = UserFactory.create_batch(3)
        owner = users[0]
        project = ProjectFactory.create(published=True)
        TaskRunFactory.create(user=users[1], project=project)

        url = '/project/%s/performancestats?api_key=%s' % (project.short_name, owner.api_key)
        res = self.app_get_json(url)

        data = json.loads(res.data)
        data['contributors'] == [], data['contributors']
