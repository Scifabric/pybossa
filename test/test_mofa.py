from factories import AppFactory
from pybossa.core import db
from default import Test

class TestMofa(Test):
    def test_one(self):
        app = AppFactory.build()
        print app in db.session
        assert False
