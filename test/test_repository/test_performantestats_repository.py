from default import Test, db, with_context
from factories import PerformanceStatsFactory, UserFactory, ProjectFactory
from pybossa.repositories import PerformanceStatsRepository
from pybossa.exc import DBIntegrityError
from nose.tools import assert_raises


class TestPerformanceStatsRepository(Test):

    def setUp(self):
        super(TestPerformanceStatsRepository, self).setUp()
        self.repo = PerformanceStatsRepository(db)

    @with_context
    def test_save_integrity_error(self):
        stat = PerformanceStatsFactory.build()
        assert_raises(DBIntegrityError, self.repo.save, stat)

    @with_context
    def test_update_integrity_error(self):
        user = UserFactory.create()
        project = ProjectFactory.create()
        stat = PerformanceStatsFactory.create(
            project_id = project.id,
            user_id = user.id
        )
        stat.stat_type = None
        assert_raises(DBIntegrityError, self.repo.update, stat)
