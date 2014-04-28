from default import Test, db
from factories import UserFactory, AppFactory, CategoryFactory, BlogpostFactory, TaskFactory, TaskRunFactory
from pybossa.model.user import User
from pybossa.model.category import Category
from pybossa.model.task import Task
from pybossa.model.task_run import TaskRun

class TestFactories(Test):

    # def test_user(self):
    #     user = UserFactory.build()
    #     user2 = UserFactory.create()

    #     assert True

    # def test_app(self):
    #     app = AppFactory.create()
    #     print app
    #     app2 = AppFactory.create(category=app.category)
    #     print app2
    #     print app2.owner
    #     print db.session.query(Category).all()

    #     assert True

    # def test_blogpost(self):
    #     blogpost = BlogpostFactory.create()

    #     print blogpost

    #     print db.session.query(User).all()[0]
    #     print db.session.query(User).all()[1]

    #     assert True

    # def test_task_run(self):
    #     app = AppFactory.create(owner__name='Axeindren')
    #     task = TaskFactory.create(app=app)
    #     taskrun = TaskRunFactory.create_batch(10, task=task, app=app)

    #     task = db.session.query(Task).all()
    #     for t in taskrun:
    #         print t.app.owner.name
    #     print taskrun
    #     print db.session.identity_map.keys()

    #     assert False

    def test_dependencies(self):
        app = TaskRunFactory.create()
        db.session.flush()
        for item in db.session:
            print item
        assert False, db.session.identity_map.keys()