from datetime import datetime, timedelta

from mock import patch
from pybossa.task_creator_helper import _get_task_expiration


def are_almost_equal(date1, date2):
    c1 = date1 < date2 + timedelta(hours=1)
    c2 = date1 > date2 - timedelta(hours=1)
    return c1 and c2


def to_datetime(timestamp):
    return datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%S.%f')


class TestGetTaskExpirationDatetime(object):

    def test_current_expiration_is_before(self):
        now = datetime.utcnow()
        current_exp = now + timedelta(days=30)
        exp = _get_task_expiration(current_exp, 60)
        assert exp == current_exp

    def test_current_expiration_is_after(self):
        now = datetime.utcnow()
        current_exp = now + timedelta(days=90)
        exp = _get_task_expiration(current_exp, 60)
        assert are_almost_equal(exp, now + timedelta(days=60))

    def test_current_expiration_is_none(self):
        now = datetime.utcnow()
        exp = _get_task_expiration(None, 60)
        assert are_almost_equal(exp, now + timedelta(days=60))


class TestGetTaskExpirationString(object):

    def test_current_expiration_is_before(self):
        now = datetime.utcnow()
        current_exp = now + timedelta(days=30)
        exp = _get_task_expiration(current_exp.isoformat(), 60)
        assert to_datetime(exp) == current_exp

    def test_current_expiration_is_after(self):
        now = datetime.utcnow()
        current_exp = now + timedelta(days=90)
        exp = _get_task_expiration(current_exp.isoformat(), 60)
        assert are_almost_equal(
            to_datetime(exp), now + timedelta(days=60))
