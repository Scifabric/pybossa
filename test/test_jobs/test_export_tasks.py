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
