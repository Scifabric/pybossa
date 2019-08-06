
from pybossa.wizard import Wizard
from default import Test, with_context
from collections import OrderedDict


class WizardTestHelper(Test):
    def get_wizard_steps(self):
        return OrderedDict([
            ('step_one', {
                'title': 'Step One',
                'icon': 'fa fa-pencil',
                'href': {'url_for': 'project.new',
                         'args': ['']},
                'done_checks': {'always': False},
                'enable_checks': {'always': True},
                'visible_checks': {'always': True},
            }),
            ('ext_config', {
                'title': 'External Configuration',
                'icon': 'fa fa-cogs',
                'href': {'url_for': 'project.ext_config',
                         'args': ['short_name']},
                'done_checks': {'and': ['ext_config'], 'or': []},
                'enable_checks': {'and': ['project_exist'], 'or': []},
                'visible_checks': {'always': True},
                'config_for_checks': {
                    'condition': {'and': ['tracking_id'], 'or': ['hdfs', 'gigwork_poller']},
                    'attrs': {'tracking_id': 'info.ext_config.data_access.tracking_id',
                              'hdfs': 'info.ext_config.hdfs.path',
                              'gigwork_poller': 'info.ext_config.gigwork_poller.target_bucket'}}}),
            ('publish', {
                'title': 'Publish',
                'icon': 'fa fa-check',
                'href': {'url_for': 'project.publish',
                         'args': ['short_name', 'published']},
                'done_checks': {'always': False},
                'enable_checks': {'and': ['task_presenter', 'tasks_amount', 'ext_config'], 'or': ['project_publish']},
                'visible_checks': {'always': True}}),
            ('step_hide', {
                'title': 'Publish',
                'icon': 'fa fa-check',
                'href': {'url_for': 'project.publish',
                         'args': ['short_name', 'published']},
                'done_checks': {'always': False},
                'enable_checks': {'and': ['task_presenter', 'tasks_amount', 'ext_config'], 'or': ['project_publish']},
                'visible_checks': {'always': False}})])

    def get_project(self):
        project = dict(
            published=True,
            n_tasks=1,
            id=1,
            short_name='project1',
            info=dict(ext_config={'hdfs': {'path': 'hdfs/path/test'},
                                  'gigwork_poller': {'target_bucket': 'bcos-test'},
                                  'data_access': {'tracking_id': '4545'}}))

        return project

    def get_request(self):
        return dict(url='test/url',
                    path='test/path')


class TestWizard(WizardTestHelper):

    def test_wizard_checks_project_is_none(self):
        project_none = None
        project_wizard = Wizard(project_none, self.get_wizard_steps(), self.get_request())
        assert project_wizard.project_exist() is False
        assert project_wizard.not_project_exist() is True
        assert project_wizard.ext_config() is False
        assert project_wizard.tasks_amount() is False
        assert project_wizard.project_publish() is False
        assert project_wizard.task_guidelines() is False
        assert project_wizard.task_presenter() is False


    @with_context
    def test_wizard_with_project(self):
        project = self.get_project()
        project['info']['task_presenter'] = 'Content'
        project['info']['task_guidelines'] = 'Content'
        project_wizard = Wizard(project, self.get_wizard_steps(), self.get_request())
        assert project_wizard.project_exist() is True
        assert project_wizard.not_project_exist() is False
        assert project_wizard.ext_config() is True
        assert project_wizard.tasks_amount() is True
        assert project_wizard.project_publish() is True
        assert project_wizard.task_guidelines() is True
        assert project_wizard.task_presenter() is True
        assert project_wizard.not_project_publish() is False

    @with_context
    def test_wizard_get_href_project(self):
        project_wizard = Wizard(self.get_project(), self.get_wizard_steps(), self.get_request())
        assert project_wizard.get_href({}, False) == ''
        href = {'url_for': 'project.publish',
                'args': ['short_name', 'published']}
        assert project_wizard.get_href(href, True).endswith('project1/1/publish'), 'project1/1/publish'

        href = {'url_for': 'project.new',
                'args': ['']}
        assert project_wizard.get_href(href, True).endswith('project/new'), 'project/new'

        href = {'url_for': 'project.ext_config',
                'args': ['short_name']}
        assert project_wizard.get_href(href, True).endswith('project1/ext-config'), 'project1/ext-config'

    @with_context
    def test_wizard_run_checks_project(self):
        project = self.get_project()
        project['info']['task_presenter'] = ''
        project['info']['task_guidelines'] = ''

        project_wizard = Wizard(project, self.get_wizard_steps(), self.get_request())
        conditions = {'always': True,
                      'and': ['task_presenter', 'tasks_amount', 'ext_config'],
                      'or': ['project_publish']}
        assert project_wizard.run_checks(conditions) is True

        conditions = {'and': ['tasks_amount'],
                      'or': []}
        assert project_wizard.run_checks(conditions) is True

        conditions = {'and': [],
                      'or': ['tasks_amount']}
        assert project_wizard.run_checks(conditions) is True

        conditions = {'and': ['task_presenter'],
                      'or': ['tasks_amount']}
        assert project_wizard.run_checks(conditions) is True

        conditions = {'and': ['tasks_amount'],
                      'or': ['task_presenter']}
        assert project_wizard.run_checks(conditions) is True

        conditions = {'and': ['task_presenter', 'tasks_amount'],
                      'or': ['task_presenter']}
        assert project_wizard.run_checks(conditions) is False

        conditions = {'and': ['task_presenter', 'tasks_amount'],
                      'or': ['task_presenter', 'tasks_amount']}
        assert project_wizard.run_checks(conditions) is True

        conditions = {'and': ['task_presenter'],
                      'or': ['task_presenter']}
        assert project_wizard.run_checks(conditions) is False

        conditions = {'and': ['task_guidelines'],
                      'or': []}
        assert project_wizard.run_checks(conditions) is False

        project['info']['task_presenter'] = 'Content'
        project['info']['task_guidelines'] = 'Content'
        project_wizard = Wizard(project, self.get_wizard_steps(), self.get_request())

        conditions = {'and': ['task_guidelines', 'task_guidelines'],
                      'or': []}
        assert project_wizard.run_checks(conditions) is True

    @with_context
    def test_wizard_get_nested_keys(self):
        project_wizard = Wizard(self.get_project(), self.get_wizard_steps(), self.get_request())
        assert project_wizard.get_nested_keys('info.ext_config.gigwork_poller.target_bucket') == 'bcos-test'

    @with_context
    def test_wizard_get_wizard_list(self):
        project_wizard = Wizard(self.get_project(), self.get_wizard_steps(), self.get_request())
        expected_list = [
            {'active': False,
             'enable': True,
             'done': False,
             'title': 'Step One',
             'href': 'http://localhost/project/new',
             'icon': 'fa fa-pencil'},
            {'active': False,
             'enable': True,
             'done': True,
             'title': 'External Configuration',
             'href': 'http://localhost/project/project1/ext-config',
             'icon': 'fa fa-cogs'},
            {'active': False,
             'enable': True,
             'done': False,
             'title': 'Publish',
             'href': 'http://localhost/project/project1/1/publish',
             'icon': 'fa fa-check'}]
        assert project_wizard.get_wizard_list() == expected_list
