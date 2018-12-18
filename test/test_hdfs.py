from subprocess import CalledProcessError
from nose.tools import assert_raises
from default import flask_app, sentinel, with_context, rebuild_db
from factories import ProjectFactory, UserFactory
from mock import patch, MagicMock

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

    @with_context
    @patch('pybossa.hdfs.client.check_call')
    def test_kinit_error(self, subprocess):
        client = HDFSKerberos('testurl', 'testuser')
        subprocess.side_effect = [CalledProcessError('', ''), CalledProcessError('', '')]
        assert_raises(CalledProcessError, client.get_ticket)

    @with_context
    @patch('pybossa.hdfs.client.check_call')
    def test_get(self, subprocess):
        reader = MagicMock()
        reader.read.return_value = 'abc'
        reader.__enter__.return_value = reader
        def read(*args, **kwargs):
            return reader
        client = HDFSKerberos('testurl', 'testuser')
        with patch.object(client, 'read', read):
            assert client.get('test') == 'abc'

    @with_context
    @patch('pybossa.hdfs.client.check_call')
    def test_put(self, subprocess):
        client = HDFSKerberos('testurl', 'testuser')
        writer = MagicMock()
        with patch.object(client, 'write'):
            client.put('test', 'hello')
            client.write.assert_called()
