
import json
from helper import web
from default import with_context
from factories import TaskFactory, ProjectFactory, TaskRunFactory, UserFactory
from pybossa.core import user_repo
from nose.tools import assert_raises

class QuizTest(web.Helper):

    def create_project_and_user(self, short_circuit=None):
        admin = UserFactory.create()
        user = UserFactory.create()
        project_quiz = {
            'enabled':True,
            'questions':10,
            'passing':7
        }
        if short_circuit is not None:
            project_quiz['short_circuit'] = short_circuit

        project = ProjectFactory.create(
            owner=admin,
            published=True,
            info=dict(quiz=project_quiz, enable_gold=False))
        self.set_proj_passwd_cookie(project, user=user)
        self.signin_user(user)
        return project, user


class TestScheduler(QuizTest):

    @with_context
    def test_only_golden_when_quiz_in_progress(self):
        '''Test that user only receives golden tasks while quiz is in progress'''
        project, user = self.create_project_and_user()
        golden_tasks = TaskFactory.create_batch(10, project=project, n_answers=1, calibration=1)
        non_golden_tasks = TaskFactory.create_batch(10, project=project, n_answers=1, calibration=0)
        url = '/api/project/{}/newtask'.format(project.id)
        response = self.app.get(url)
        task = json.loads(response.data)
        assert any(task['id'] == golden_task.id for golden_task in golden_tasks)

    @with_context
    def test_failed_quiz_no_task(self):
        '''Test that user receives no tasks if they failed the quiz'''
        project, user = self.create_project_and_user()
        golden_tasks = TaskFactory.create_batch(10, project=project, n_answers=1, calibration=1)
        non_golden_tasks = TaskFactory.create_batch(10, project=project, n_answers=1, calibration=0)
        user.set_quiz_status(project, 'failed')

        url = '/api/project/{}/newtask'.format(project.id)
        response = self.app.get(url)
        task = json.loads(response.data)
        assert not task # task == {}

    @with_context
    def test_passed_quiz_normal_task(self):
        '''Test that user receives normal tasks if they have passed the quiz'''
        project, user = self.create_project_and_user()
        golden_tasks = TaskFactory.create_batch(10, project=project, n_answers=1, calibration=1)
        non_golden_tasks = TaskFactory.create_batch(10, project=project, n_answers=1, calibration=0)
        user.set_quiz_status(project, 'passed')

        url = '/api/project/{}/newtask'.format(project.id)
        response = self.app.get(url)
        task = json.loads(response.data)
        assert any(task['id'] == non_golden_task.id for non_golden_task in non_golden_tasks)


class TestQuizUpdate(QuizTest):

    @with_context
    def test_wrong_answer_count_update(self):
        '''Test user quiz wrong answer count increments when task run with wrong answer is submitted'''
        project, user = self.create_project_and_user()
        task_answers = {}
        for i in range(10):
            gold_answers = {'answer':i}
            golden_task = TaskFactory.create(project=project, n_answers=1, calibration=1, gold_answers=gold_answers)
            task_answers[golden_task.id] = gold_answers

        non_golden_tasks = TaskFactory.create_batch(10, project=project, n_answers=1, calibration=0)

        quiz = user.get_quiz_for_project(project)
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
        updated_quiz = user.get_quiz_for_project(project)
        assert updated_quiz['result']['wrong'] == quiz['result']['wrong'] + 1
        assert updated_quiz['result']['right'] == quiz['result']['right']

    @with_context
    def test_right_answer_count_update(self):
        '''Test user quiz right answer count increments when task run with right answer is submitted'''
        project, user = self.create_project_and_user()
        task_answers = {}
        for i in range(10):
            gold_answers = {'answer':i}
            golden_task = TaskFactory.create(project=project, n_answers=1, calibration=1, gold_answers=gold_answers)
            task_answers[golden_task.id] = gold_answers

        non_golden_tasks = TaskFactory.create_batch(10, project=project, n_answers=1, calibration=0)

        quiz = user.get_quiz_for_project(project)
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
        updated_quiz = user.get_quiz_for_project(project)
        assert updated_quiz['result']['wrong'] == quiz['result']['wrong']
        assert updated_quiz['result']['right'] == quiz['result']['right'] + 1

    @with_context
    def test_status_update_on_pass(self):
        '''Test user quiz status transitions to passed once right answer count exceeds threshold'''
        project, user = self.create_project_and_user()
        task_answers = {}
        for i in range(10):
            gold_answers = {'answer':i}
            golden_task = TaskFactory.create(project=project, n_answers=1, calibration=1, gold_answers=gold_answers)
            task_answers[golden_task.id] = gold_answers

        non_golden_tasks = TaskFactory.create_batch(10, project=project, n_answers=1, calibration=0)

        quiz = user.get_quiz_for_project(project)

        user.set_quiz_for_project(
            project.id,
            {
                'status':'in_progress',
                'result':{
                    'right': quiz['config']['passing'] - 1,
                    'wrong': 0
                },
                'config': quiz['config']
            }
        )
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
        updated_quiz = user.get_quiz_for_project(project)
        assert updated_quiz['status'] == 'passed'
        assert user.get_quiz_passed(project)

    @with_context
    def test_status_update_on_fail(self):
        '''Test user quiz status transitions to failed once quiz is complete and wrong answer count exceeds limit'''
        project, user = self.create_project_and_user()
        task_answers = {}
        for i in range(10):
            gold_answers = {'answer':i}
            golden_task = TaskFactory.create(project=project, n_answers=1, calibration=1, gold_answers=gold_answers)
            task_answers[golden_task.id] = gold_answers

        non_golden_tasks = TaskFactory.create_batch(10, project=project, n_answers=1, calibration=0)
        quiz = user.get_quiz_for_project(project)

        user.set_quiz_for_project(
            project.id,
            {
                'status':'in_progress',
                'result':{
                    'right': quiz['config']['passing'] - 1,
                    'wrong': quiz['config']['questions'] - quiz['config']['passing']
                },
                'config': quiz['config']
            }
        )
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
        updated_quiz = user.get_quiz_for_project(project)
        assert updated_quiz['status'] == 'failed'
        assert user.get_quiz_failed(project)

    @with_context
    def test_cannot_update_passed_quiz(self):
        '''Test exception raised when updating results for quiz that has already passed'''
        project, user = self.create_project_and_user()
        user.set_quiz_status(project, 'passed')
        assert_raises(Exception, lambda: user.add_quiz_right_answer(project) )
        assert_raises(Exception, lambda: user.add_quiz_wrong_answer(project) )

    @with_context
    def test_cannot_update_failed_quiz(self):
        '''Test exception raised when updating results for quiz that has already failed'''
        project, user = self.create_project_and_user()
        user.set_quiz_status(project, 'failed')
        assert_raises(Exception, lambda: user.add_quiz_right_answer(project) )
        assert_raises(Exception, lambda: user.add_quiz_wrong_answer(project) )

    @with_context
    def test_reset_quiz(self):
        '''Test reset_quiz() resets quiz'''
        project, user = self.create_project_and_user()
        user.set_quiz_for_project(
            project.id,
            {
                'status': 'passed',
                'result': {
                    'right': 1,
                    'wrong': 2
                }
            }
        )
        user.reset_quiz(project)
        quiz = user.get_quiz_for_project(project)
        assert quiz == {
            'status': 'in_progress',
            'result': {
                'right': 0,
                'wrong': 0
            },
            'config': quiz['config']
        }, quiz

    @with_context
    def test_reset_non_existent_quiz(self):
        '''Test reset_quiz() does not error if there is no quiz'''
        project, user = self.create_project_and_user()
        user.reset_quiz(project)

    @with_context
    def test_completion_mode_all_questions(self):
        '''Test quiz does not end until all questions have been presented'''
        project, user = self.create_project_and_user(short_circuit=False)
        task_answers = {}
        quiz = project.get_quiz()

        for i in range(quiz['questions']):
            gold_answers = {'answer':i}
            golden_task = TaskFactory.create(project=project, n_answers=1, calibration=1, gold_answers=gold_answers)
            task_answers[golden_task.id] = gold_answers

        def submit_wrong_answer():
            new_task_url = '/api/project/{}/newtask'.format(project.id)
            new_task_response = self.app.get(new_task_url)
            task = json.loads(new_task_response.data)
            task_run_url = '/api/taskrun'
            task_run_data = {
                'project_id': project.id,
                'task_id': task['id'],
                'info': {'answer': 'wrong'}
            }
            return self.app.post(
                task_run_url,
                data=json.dumps(task_run_data)
            )

        for _ in range(quiz['questions'] - 1):
            submit_wrong_answer()
            updated_quiz = user.get_quiz_for_project(project)
            assert updated_quiz['status'] == 'in_progress'

        submit_wrong_answer()
        updated_quiz = user.get_quiz_for_project(project)
        assert updated_quiz['status'] == 'failed'

