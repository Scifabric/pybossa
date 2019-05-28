from default import Test, db, with_context
from factories import PerformanceStatsFactory, UserFactory, ProjectFactory
from pybossa.repositories import PerformanceStatsRepository
from pybossa.model.performance_stats import StatType
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

    @with_context
    def test_delete(self):
        user = UserFactory.create()
        project = ProjectFactory.create()
        stat = PerformanceStatsFactory.create(
            project_id = project.id,
            user_id = user.id
        )
        self.repo.bulk_delete(project, stat.field, stat.stat_type)
        deleted = self.repo.get(stat.id)
        assert deleted is None

    @with_context
    def test_delete_for_project_multiple(self):
        user = UserFactory.create()
        projects = ProjectFactory.create_batch(2)
        for p in projects:
            stat = PerformanceStatsFactory.create(
                project_id = p.id,
                user_id = user.id
            )
        assert len(self.repo.filter_by(user_id=user.id)) == 2
        self.repo.bulk_delete(projects[0], stat.field, stat.stat_type)
        stats = self.repo.filter_by(user_id=user.id)
        assert len(stats) == 1
        assert all(stat.project_id == projects[1].id for stat in stats)

    @with_context
    def test_delete_for_project_user(self):
        users = UserFactory.create_batch(2)
        projects = ProjectFactory.create_batch(2)
        types = [StatType.confusion_matrix, StatType.accuracy]
        for p in projects:
            for u in users:
                for t in types:
                    stat = PerformanceStatsFactory.create_batch(
                        2,
                        project_id = p.id,
                        user_id = u.id,
                        stat_type = t
                    )

        assert len(self.repo.filter_by()) == 16
        _type = types[0]
        user = users[0]
        project = projects[0]
        self.repo.bulk_delete(project, stat[0].field, _type, user_id=user.id)
        stats = self.repo.filter_by()
        assert len(stats) == 14
        assert all(
            stat.user_id != user.id or
            stat.project_id != project.id or
            stat.stat_type != _type for stat in stats)
