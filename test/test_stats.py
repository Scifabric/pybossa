import datetime
import time
from base import web, model, db, Fixtures
import pybossa.stats as stats


class TestAdmin:
    def setUp(self):
        self.app = web.app
        model.rebuild_db()
        Fixtures.create()

    def tearDown(self):
        db.session.remove()

    @classmethod
    def teardown_class(cls):
        model.rebuild_db()

    # Tests
    # Fixtures will create 10 tasks and will need 10 answers per task, so
    # the app will be completed when 100 tasks have been submitted
    # Only 10 task_runs are saved in the DB

    def test_00_avg_n_tasks(self):
        """Test STATS avg and n of tasks method works"""
        with self.app.test_request_context('/'):
            avg, n_tasks = stats.get_avg_n_tasks(1)
            err_msg = "The average number of answer per task is wrong"
            assert avg == 10, err_msg
            err_msg = "The n of tasks is wrong"
            assert n_tasks == 10, err_msg

    def test_01_stats_dates(self):
        """Test STATS dates method works"""
        today = unicode(datetime.date.today())
        with self.app.test_request_context('/'):
            dates, dates_n_tasks, dates_anon, dates_auth = stats.stats_dates(1)
            err_msg = "There should be 10 answers today"
            assert dates[today] == 10, err_msg
            err_msg = "There should be 100 answers per day"
            assert dates_n_tasks[today] == 100, err_msg
            err_msg = "The SUM of answers from anon and auth users should be 10"
            assert (dates_anon[today] + dates_auth[today]) == 10, err_msg

    def test_02_stats_hours(self):
        """Test STATS hours method works"""
        hour = unicode(datetime.datetime.today().strftime('%H'))
        with self.app.test_request_context('/'):
            hours, hours_anon, hours_auth, max_hours,\
                max_hours_anon, max_hours_auth = stats.stats_hours(1)
            for i in range(0, 24):
                # There should be only 10 answers at current hour
                if str(i) == hour:
                    assert hours[str(i)] == 10, "There should be 10 answers"
                else:
                    assert hours[str(i)] == 0, "There should be 0 answers"

                if str(i) == hour:
                    tmp = (hours_anon[hour] + hours_auth[hour])
                    assert tmp == 10, "There should be 10 answers"
                else:
                    tmp = (hours_anon[str(i)] + hours_auth[str(i)])
                    assert tmp == 0, "There should be 0 answers"
            err_msg = "It should be 10, as all answer are done in the same hour"
            assert max_hours == 10, err_msg
            assert (max_hours_anon + max_hours_auth) == 10, err_msg

    def test_03_stats(self):
        """Test STATS stats method works"""
        today = unicode(datetime.date.today())
        hour = int(datetime.datetime.today().strftime('%H'))
        date_ms = time.mktime(time.strptime(today, "%Y-%m-%d")) * 1000
        anon = 0
        auth = 0
        with self.app.test_request_context('/'):
            dates_stats, hours_stats, user_stats = stats.get_stats(1)
            for item in dates_stats:
                if item['label'] == 'Anon + Auth':
                    assert item['values'][0][0] == date_ms, item['values'][0][0]
                    assert item['values'][0][1] == 10, "There should be 10 answers"
                if item['label'] == 'Anonymous':
                    assert item['values'][0][0] == date_ms, item['values'][0][0]
                    anon = item['values'][0][1]
                if item['label'] == 'Authenticated':
                    assert item['values'][0][0] == date_ms, item['values'][0][0]
                    auth = item['values'][0][1]
                if item['label'] == 'Total':
                    assert item['values'][0][0] == date_ms, item['values'][0][0]
                    assert item['values'][0][1] == 10, "There should be 10 answers"
                if item['label'] == 'Expected Answers':
                    assert item['values'][0][0] == date_ms, item['values'][0][0]
                    for i in item['values']:
                        assert i[1] == 100, "Each date should have 100 answers"
                    assert item['values'][0][1] == 100, "There should be 10 answers"
                if item['label'] == 'Estimation':
                    assert item['values'][0][0] == date_ms, item['values'][0][0]
                    v = 10
                    for i in item['values']:
                        assert i[1] == v, "Each date should have 10 extra answers"
                        v = v + 10
            assert auth + anon == 10, "date stats sum of auth and anon should be 10"

            max_hours = 0
            for item in hours_stats:
                if item['label'] == 'Anon + Auth':
                    max_hours = item['max']
                    assert item['max'] == 10, "Max hours value should be 10"
                    for i in item['values']:
                        if i[0] == hour:
                            assert i[1] == 10, "There should be 10 answers"
                            assert i[2] == 5, "The size of the bubble should be 5"
                        else:
                            assert i[1] == 0, "There should be 0 answers"
                            assert i[2] == 0, "The size of the buggle should be 0"
                if item['label'] == 'Anonymous':
                    anon = item['max']
                    for i in item['values']:
                        if i[0] == hour:
                            assert i[1] == anon, "There should be anon answers"
                            assert i[2] == (anon * 5) / max_hours, "The size of the bubble should be 5"
                        else:
                            assert i[1] == 0, "There should be 0 answers"
                            assert i[2] == 0, "The size of the buggle should be 0"
                if item['label'] == 'Authenticated':
                    auth = item['max']
                    for i in item['values']:
                        if i[0] == hour:
                            assert i[1] == auth, "There should be anon answers"
                            assert i[2] == (auth * 5) / max_hours, "The size of the bubble should be 5"
                        else:
                            assert i[1] == 0, "There should be 0 answers"
                            assert i[2] == 0, "The size of the buggle should be 0"
            assert auth + anon == 10, "date stats sum of auth and anon should be 10"

            err_msg = "date stats sum of auth and anon should be 10"
            assert user_stats['n_anon'] + user_stats['n_auth'], err_msg
