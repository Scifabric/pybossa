from subprocess import CalledProcessError
from default import flask_app, sentinel, with_context, rebuild_db
from factories import ProjectFactory, UserFactory
from mock import patch

from pybossa.hdfs.client import HDFSKerberos

class TestHdfsAuth(object):

    @patch('pybossa.hdfs.client.check_call')
    def test_init_not_needed(self, subprocess):
        client = HDFSKerberos('testurl', 'testuser')
        client.get_ticket()
        subprocess.return_value = 0
        assert subprocess.call_count == 1


    @with_context
    @patch('pybossa.hdfs.client.check_call')
    def test_init_needed(self, subprocess):
        client = HDFSKerberos('testurl', 'testuser')
        subprocess.side_effect = [CalledProcessError('', ''), 0]
        client.get_ticket()
        assert subprocess.call_count == 2