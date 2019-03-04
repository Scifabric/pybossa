from default import Test, with_context, flask_app
from factories import ProjectFactory, UserFactory, TaskFactory, TaskRunFactory
from pybossa.jobs import export_tasks
from mock import patch, MagicMock
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
    @unittest.skip("Skipping Test until we make flatten available")
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

        fp = StringIO(message.attachments[0].data)
        zfp = zipfile.ZipFile(fp, "r")
        file_objects = zfp.infolist()
        contents = [zfp.read(file_object) for file_object in file_objects]
        expected_headers = [
            'task_run__calibration', 'task_run__created',
            'task_run__external_uid', 'task_run__finish_time',
            'task_run__id', 'task_run__info', 'task_run__info__list',
            'task_run__info__list__0__lastName', 'task_run__info__list__0__name',
            'task_run__info__list__1__lastName', 'task_run__info__list__1__name',
            'task_run__info__object', 'task_run__info__object__a',
            'task_run__info__text', 'task_run__project_id', 'task_run__task__gold_answers',
            'task_run__task_id', 'task_run__timeout', 'task_run__user_id',
            'task_run__user_ip']
        assert all(header in contents[0] for header in expected_headers)
              
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
