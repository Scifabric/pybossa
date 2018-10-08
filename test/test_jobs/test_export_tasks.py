from default import Test, with_context, flask_app
from factories import ProjectFactory, UserFactory, TaskFactory, TaskRunFactory
from pybossa.jobs import export_tasks
from mock import patch, MagicMock
from unidecode import unidecode


class TestExport(Test):

    @with_context
    @patch('pybossa.jobs.mail')
    def test_export_tasks_consensus_csv(self, mail):
        """Test JOB export_tasks consensus works."""
        user = UserFactory.create(admin=True)
        project = ProjectFactory.create(name='test_project')
        task = TaskFactory.create(project=project)
        task_run = TaskRunFactory.create(project=project, task=task)

        export_tasks(user.email_addr, project.short_name, 'consensus', False, 'csv')
        args, kwargs = mail.send.call_args
        message = args[0]
        assert message.recipients[0] == user.email_addr, message.recipients
        assert message.subject == 'Data exported for your project: test_project', message.subject

        attachment = message.attachments[0]
        proj_name = unidecode(project.short_name)
        filename = '{}_{}'.format(project.id, proj_name)
        assert attachment.filename == '{}_consensus_csv.zip'.format(filename)

    @with_context
    @patch('pybossa.jobs.mail')
    def test_export_tasks_consensus_csv_metadata(self, mail):
        """Test JOB export_tasks consensus and metadata works."""
        user = UserFactory.create(admin=True)
        project = ProjectFactory.create(name='test_project')
        task = TaskFactory.create(project=project)
        task_run = TaskRunFactory.create(project=project, task=task)

        export_tasks(user.email_addr, project.short_name, 'consensus', True, 'csv')
        args, kwargs = mail.send.call_args
        message = args[0]
        assert message.recipients[0] == user.email_addr, message.recipients
        assert message.subject == 'Data exported for your project: test_project', message.subject

        attachment = message.attachments[0]
        proj_name = unidecode(project.short_name)
        filename = '{}_{}'.format(project.id, proj_name)
        assert attachment.filename == '{}_consensus_csv.zip'.format(filename)

    @with_context
    @patch('pybossa.jobs.mail')
    def test_export_tasks_consensus_json(self, mail):
        """Test JOB export_tasks consensus json works."""
        user = UserFactory.create(admin=True)
        project = ProjectFactory.create(name='test_project')
        task = TaskFactory.create(project=project)
        task_run = TaskRunFactory.create(project=project, task=task)

        export_tasks(user.email_addr, project.short_name, 'consensus', False, 'json')
        args, kwargs = mail.send.call_args
        message = args[0]
        assert message.recipients[0] == user.email_addr, message.recipients
        assert message.subject == 'Data exported for your project: test_project', message.subject

        attachment = message.attachments[0]
        proj_name = unidecode(project.short_name)
        filename = '{}_{}'.format(project.id, proj_name)
        assert attachment.filename == '{}_consensus_json.zip'.format(filename)

    @with_context
    @patch('pybossa.jobs.mail')
    def test_export_tasks_csv_json(self, mail):
        """Test JOB export_tasks task csv works."""
        user = UserFactory.create(admin=True)
        project = ProjectFactory.create(name='test_project')
        task = TaskFactory.create(project=project)
        task_run = TaskRunFactory.create(project=project, task=task)

        export_tasks(user.email_addr, project.short_name, 'task', False, 'csv')
        args, kwargs = mail.send.call_args
        message = args[0]
        assert message.recipients[0] == user.email_addr, message.recipients
        assert message.subject == 'Data exported for your project: test_project', message.subject

        attachment = message.attachments[0]
        proj_name = unidecode(project.short_name)
        filename = '{}_{}'.format(project.id, proj_name)
        assert attachment.filename == '{}_task_csv.zip'.format(filename)

        export_tasks(user.email_addr, project.short_name, 'task', False, 'json')
        args, kwargs = mail.send.call_args
        message = args[0]
        assert message.recipients[0] == user.email_addr, message.recipients
        assert message.subject == 'Data exported for your project: test_project', message.subject

        attachment = message.attachments[0]
        assert attachment.filename == '{}_task_json.zip'.format(filename)

        export_tasks(user.email_addr, project.short_name, 'task_run', False, 'csv')
        args, kwargs = mail.send.call_args
        message = args[0]
        assert message.recipients[0] == user.email_addr, message.recipients
        assert message.subject == 'Data exported for your project: test_project', message.subject

        attachment = message.attachments[0]
        assert attachment.filename == '{}_task_run_csv.zip'.format(filename)

        export_tasks(user.email_addr, project.short_name, 'task_run', False, 'json')
        args, kwargs = mail.send.call_args
        message = args[0]
        assert message.recipients[0] == user.email_addr, message.recipients
        assert message.subject == 'Data exported for your project: test_project', message.subject

        attachment = message.attachments[0]
        assert attachment.filename == '{}_task_run_json.zip'.format(filename)

        filters = dict(task_id=1,hide_completed=True,pcomplete_from='2018-01-01T00:00:00.0001',
            pcomplete_to='2018-12-12T00:00:00.0001', priority_from=0.0, priority_to=0.5,
            created_from='2018-01-01T00:00:00.0001', created_to='2018-12-12T00:00:00.0001')

        filters = {'display_info_columns': [], 'pcomplete_from': 0.0, 'pcomplete_to': 0.45}
        export_tasks(user.email_addr, project.short_name, 'task', False, 'csv', filters)
        args, kwargs = mail.send.call_args
        message = args[0]
        assert message.recipients[0] == user.email_addr, message.recipients
        assert message.subject == 'Data exported for your project: test_project', message.subject

        export_tasks(user.email_addr, project.short_name, 'task', False, 'json', filters)
        args, kwargs = mail.send.call_args
        message = args[0]
        assert message.recipients[0] == user.email_addr, message.recipients
        assert message.subject == 'Data exported for your project: test_project', message.subject
