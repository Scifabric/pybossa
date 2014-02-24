import json
from test_api import TestAPI


class TestGlobalStatsAPI(TestAPI):
    def test_global_stats(self):
        """Test Global Stats works."""
        res = self.app.get('api/globalstats')
        stats = json.loads(res.data)
        assert res.status_code == 200, res.status_code
        keys = ['n_projects', 'n_pending_tasks', 'n_users', 'n_task_runs']
        for k in keys:
            err_msg = "%s should be in stats JSON object" % k
            assert k in stats.keys(), err_msg

    def test_post_global_stats(self):
        """Test Global Stats Post works."""
        res = self.app.post('api/globalstats')
        assert res.status_code == 405, res.status_code