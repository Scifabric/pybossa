
import json
from helper import web
from default import with_context
from factories import TaskFactory, ProjectFactory, TaskRunFactory, UserFactory
from pybossa.core import user_repo
from nose.tools import assert_raises

class TestScheduler(web.Helper):

    @with_context
    def test_only_golden_when_quiz_in_progress(self):
        '''Test that user only receives golden tasks while quiz is in progress'''
        admin = UserFactory.create()
        self.signin_user(admin)
        project_quiz = dict(
            enabled=True,
            questions_per_quiz=10,
            correct_answers_to_pass=7
        )
        project = ProjectFactory.create(owner=admin, info=dict(quiz=project_quiz, enable_gold=False))
        golden_tasks = TaskFactory.create_batch(10, project=project, n_answers=1, calibration=1)
        non_golden_tasks = TaskFactory.create_batch(10, project=project, n_answers=1, calibration=0)
        url = '/api/project/{}/newtask'.format(project.id)
        response = self.app.get(url)
        task = json.loads(response.data)
        assert task['calibration']

    @with_context
    def test_failed_quiz_no_task(self):
        '''Test that user receives no tasks if they failed the quiz'''
        admin = UserFactory.create()
        self.signin_user(admin)
        project_quiz = dict(
            enabled=True,
            questions_per_quiz=10,
            correct_answers_to_pass=7
        )
        project = ProjectFactory.create(owner=admin, info=dict(quiz=project_quiz, enable_gold=False))
        golden_tasks = TaskFactory.create_batch(10, project=project, n_answers=1, calibration=1)
        non_golden_tasks = TaskFactory.create_batch(10, project=project, n_answers=1, calibration=0)
        admin.set_quiz_for_project(project.id, {'status':'failed'})

        url = '/api/project/{}/newtask'.format(project.id)
        response = self.app.get(url)
        task = json.loads(response.data)
        assert not task # task == {}

    @with_context
    def test_passed_quiz_normal_task(self):
        '''Test that user receives normal tasks if they have passed the quiz'''
        admin = UserFactory.create()
        self.signin_user(admin)
        project_quiz = dict(
            enabled=True,
            questions_per_quiz=10,
            correct_answers_to_pass=7
        )
        project = ProjectFactory.create(owner=admin, info=dict(quiz=project_quiz, enable_gold=False))
        golden_tasks = TaskFactory.create_batch(10, project=project, n_answers=1, calibration=1)
        non_golden_tasks = TaskFactory.create_batch(10, project=project, n_answers=1, calibration=0)
        admin.set_quiz_for_project(project.id, {'status':'passed'})

        url = '/api/project/{}/newtask'.format(project.id)
        response = self.app.get(url)
        task = json.loads(response.data)
        assert not task['calibration']


class TestQuizUpdate(web.Helper):

    @with_context
    def test_wrong_answer_count_update(self):
        '''Test user quiz wrong answer count increments when task run with wrong answer is submitted'''
        admin = UserFactory.create()
        self.signin_user(admin)
        project_quiz = dict(
            enabled=True,
            questions_per_quiz=10,
            correct_answers_to_pass=7
        )
        project = ProjectFactory.create(owner=admin, info=dict(quiz=project_quiz, enable_gold=False))
        task_answers = {}
        for i in range(10):
            gold_answers = {'answer':i}
            golden_task = TaskFactory.create(project=project, n_answers=1, calibration=1, gold_answers=gold_answers)
            task_answers[golden_task.id] = gold_answers

        non_golden_tasks = TaskFactory.create_batch(10, project=project, n_answers=1, calibration=0)

        quiz = admin.get_quiz_for_project(project.id)
        new_task_url = '/api/project/{}/newtask'.format(project.id)
        new_task_response = self.app.get(new_task_url)
        task = json.loads(new_task_response.data)
        task_run_url = '/api/taskrun'
        task_run_data = {
            'project_id': project.id,
            'task_id': task['id'],
            'info': {'answer': 'wrong'}
        }
        task_run_response = self.app.post(
            task_run_url,
            data=json.dumps(task_run_data)
        )
        updated_quiz = admin.get_quiz_for_project(project.id)
        assert updated_quiz['result']['wrong'] == quiz['result']['wrong'] + 1
        assert updated_quiz['result']['right'] == quiz['result']['right']

    @with_context
    def test_right_answer_count_update(self):
        '''Test user quiz right answer count increments when task run with right answer is submitted'''
        admin = UserFactory.create()
        self.signin_user(admin)
        project_quiz = dict(
            enabled=True,
            questions_per_quiz=10,
            correct_answers_to_pass=7
        )
        project = ProjectFactory.create(owner=admin, info=dict(quiz=project_quiz, enable_gold=False))
        task_answers = {}
        for i in range(10):
            gold_answers = {'answer':i}
            golden_task = TaskFactory.create(project=project, n_answers=1, calibration=1, gold_answers=gold_answers)
            task_answers[golden_task.id] = gold_answers

        non_golden_tasks = TaskFactory.create_batch(10, project=project, n_answers=1, calibration=0)

        quiz = admin.get_quiz_for_project(project.id)
        new_task_url = '/api/project/{}/newtask'.format(project.id)
        new_task_response = self.app.get(new_task_url)
        task = json.loads(new_task_response.data)
        task_run_url = '/api/taskrun'
        task_run_data = {
            'project_id': project.id,
            'task_id': task['id'],
            'info': task_answers[task['id']]
        }
        task_run_response = self.app.post(
            task_run_url,
            data=json.dumps(task_run_data)
        )
        updated_quiz = admin.get_quiz_for_project(project.id)
        assert updated_quiz['result']['wrong'] == quiz['result']['wrong']
        assert updated_quiz['result']['right'] == quiz['result']['right'] + 1

    @with_context
    def test_status_update_on_pass(self):
        '''Test user quiz status transitions to passed once right answer count exceeds threshold'''
        admin = UserFactory.create()
        self.signin_user(admin)
        project_quiz = dict(
            enabled=True,
            questions_per_quiz=10,
            correct_answers_to_pass=7
        )
        project = ProjectFactory.create(owner=admin, info=dict(quiz=project_quiz, enable_gold=False))
        task_answers = {}
        for i in range(10):
            gold_answers = {'answer':i}
            golden_task = TaskFactory.create(project=project, n_answers=1, calibration=1, gold_answers=gold_answers)
            task_answers[golden_task.id] = gold_answers

        non_golden_tasks = TaskFactory.create_batch(10, project=project, n_answers=1, calibration=0)

        admin.set_quiz_for_project(
            project.id,
            {
                'status':'in_progress',
                'result':{
                    'right': project_quiz['correct_answers_to_pass'] - 1,
                    'wrong': 0
                }
            }
        )
        quiz = admin.get_quiz_for_project(project.id)
        new_task_url = '/api/project/{}/newtask'.format(project.id)
        new_task_response = self.app.get(new_task_url)
        task = json.loads(new_task_response.data)
        task_run_url = '/api/taskrun'
        task_run_data = {
            'project_id': project.id,
            'task_id': task['id'],
            'info': task_answers[task['id']]
        }
        task_run_response = self.app.post(
            task_run_url,
            data=json.dumps(task_run_data)
        )
        updated_quiz = admin.get_quiz_for_project(project.id)
        assert updated_quiz['status'] == 'passed'
        assert admin.get_quiz_passed(project.id)

    @with_context
    def test_status_update_on_fail(self):
        '''Test user quiz status transitions to failed once quiz is complete and wrong answer count exceeds limit'''
        admin = UserFactory.create()
        self.signin_user(admin)
        project_quiz = dict(
            enabled=True,
            questions_per_quiz=10,
            correct_answers_to_pass=7
        )
        project = ProjectFactory.create(owner=admin, info=dict(quiz=project_quiz, enable_gold=False))
        task_answers = {}
        for i in range(10):
            gold_answers = {'answer':i}
            golden_task = TaskFactory.create(project=project, n_answers=1, calibration=1, gold_answers=gold_answers)
            task_answers[golden_task.id] = gold_answers

        non_golden_tasks = TaskFactory.create_batch(10, project=project, n_answers=1, calibration=0)

        admin.set_quiz_for_project(
            project.id,
            {
                'status':'in_progress',
                'result':{
                    'right': project_quiz['correct_answers_to_pass'] - 1,
                    'wrong': project_quiz['questions_per_quiz'] - project_quiz['correct_answers_to_pass']
                }
            }
        )
        quiz = admin.get_quiz_for_project(project.id)
        new_task_url = '/api/project/{}/newtask'.format(project.id)
        new_task_response = self.app.get(new_task_url)
        task = json.loads(new_task_response.data)
        task_run_url = '/api/taskrun'
        task_run_data = {
            'project_id': project.id,
            'task_id': task['id'],
            'info': {'answer': 'wrong'}
        }
        task_run_response = self.app.post(
            task_run_url,
            data=json.dumps(task_run_data)
        )
        updated_quiz = admin.get_quiz_for_project(project.id)
        assert updated_quiz['status'] == 'failed'
        assert admin.get_quiz_failed(project.id)

    @with_context
    def test_cannot_update_passed_quiz(self):
        '''Test exception raised when updating results for quiz that has already passed'''
        admin = UserFactory.create()
        project_id = 7
        admin.set_quiz_for_project(project_id, {'status':'passed'})
        assert_raises(Exception, lambda: admin.add_quiz_right_answer(project_id) )
        assert_raises(Exception, lambda: admin.add_quiz_wrong_answer(project_id) )

    @with_context
    def test_cannot_update_failed_quiz(self):
        '''Test exception raised when updating results for quiz that has already failed'''
        admin = UserFactory.create()
        project_id = 7
        admin.set_quiz_for_project(project_id, {'status':'failed'})
        assert_raises(Exception, lambda: admin.add_quiz_right_answer(project_id) )
        assert_raises(Exception, lambda: admin.add_quiz_wrong_answer(project_id) )

    @with_context
    def test_reset_quiz(self):
        '''Test clear_quiz_result() resets quiz results '''
        admin = UserFactory.create()
        project_id = 7
        admin.set_quiz_for_project(
            project_id,
            {
                'status': 'passed',
                'result': {
                    'right': 1,
                    'wrong': 2
                }
            }
        )
        admin.clear_quiz_result(project_id)
        quiz = admin.get_quiz_for_project(project_id)
        assert quiz == {
            'status': 'in_progress',
            'result': {
                'right': 0,
                'wrong': 0
            }
        }
