from default import Test, with_context, flask_app
from factories import ProjectFactory, UserFactory, TaskFactory, TaskRunFactory
from pybossa.jobs import export_tasks
from mock import patch, MagicMock
from nose.tools import assert_raises
from unidecode import unidecode
from StringIO import StringIO
import zipfile
import unittest


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
        TaskRunFactory.create(project=project, task=task,
            info={'text': u'Test String', 'object': {'a': 1},
            'list': [{'name': u'Julia', 'lastName': u'Rivera'}, {'name': u'Lola', 'lastName': u'Santos'}]})

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

    @with_context
    @patch('pybossa.jobs.mail')
    @patch('pybossa.jobs.create_connection')
    def test_export_tasks_bucket(self, create_conn, mail):
        """Test JOB export_tasks to bucket works."""
        user = UserFactory.create(admin=True)
        project = ProjectFactory.create(name='test_project', info={'export-bucket': 'buck'})
        task = TaskFactory.create(project=project)
        task_run = TaskRunFactory.create(project=project, task=task)
        conn = create_conn.return_value
        buck = conn.get_bucket.return_value
        key = buck.new_key.return_value
        key.generate_url.return_value = 'https://s3.com/buck/key'

        with patch.dict(self.flask_app.config, {
            'EXPORT_MAX_SIZE': 0,
            'EXPORT_BUCKET': 'export-bucket'
        }):
            export_tasks(user.email_addr, project.short_name, 'consensus', False, 'csv')
        args, kwargs = mail.send.call_args
        message = args[0]
        assert message.recipients[0] == user.email_addr, message.recipients
        assert message.subject == 'Data exported for your project: test_project', message.subject
        assert not message.attachments
        assert 'https://s3.com/buck/key' in message.html


    @with_context
    @patch('pybossa.jobs.mail')
    @patch('pybossa.jobs.create_connection')
    def test_export_tasks_bucket_exists(self, create_conn, mail):
        """Test JOB export_tasks to bucket works."""
        user = UserFactory.create(admin=True)
        project = ProjectFactory.create(name='test_project', info={'export-bucket': 'buck'})
        task = TaskFactory.create(project=project)
        task_run = TaskRunFactory.create(project=project, task=task)
        conn = create_conn.return_value
        conn.create_bucket.side_effect = Exception
        buck = conn.get_bucket.return_value
        key = buck.new_key.return_value
        key.generate_url.return_value = 'https://s3.com/buck/key'

        with patch.dict(self.flask_app.config, {
            'EXPORT_MAX_SIZE': 0,
            'EXPORT_BUCKET': 'export-bucket'
        }):
            export_tasks(user.email_addr, project.short_name, 'consensus', False, 'csv')
        args, kwargs = mail.send.call_args
        message = args[0]
        assert message.recipients[0] == user.email_addr, message.recipients
        assert message.subject == 'Data exported for your project: test_project', message.subject
        assert not message.attachments
        assert 'https://s3.com/buck/key' in message.html

    @with_context
    @patch('pybossa.jobs.mail')
    def test_error(self, mail):
        """Test JOB export_tasks invalid type."""
        user = UserFactory.create(admin=True)
        project = ProjectFactory.create(name='test_project')
        export_tasks(user.email_addr, project.short_name, 'task', False, 'blerson')
        args, kwargs = mail.send.call_args
        message = args[0]
        assert message.recipients[0] == user.email_addr, message.recipients
        proj_name = unidecode(project.short_name)
        expected_subject = u'Data export failed for your project: {}'.format(project.name)
        assert message.subject == expected_subject, message.subject

    @with_context
    @patch('pybossa.jobs.mail')
    def test_exception(self, mail):
        """Test JOB export_tasks exception."""
        user = UserFactory.create(admin=True)
        project = ProjectFactory.create(name='test_project')
        assert_raises(AttributeError, export_tasks, user.email_addr, project.short_name, 'consensus', False, 'blerson')
        args, kwargs = mail.send.call_args
        message = args[0]
        assert message.recipients[0] == user.email_addr, message.recipients
        assert 'Email delivery failed for your project' in message.subject
