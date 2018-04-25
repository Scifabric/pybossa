from mock import patch
from default import Test
from pybossa.uploader import cloud_jwt


class TestS3Uploader(Test):

    @patch('pybossa.uploader.cloud_jwt.jwt.encode')
    def test_jwt_value(self, encode):
        jwt_config = (
                ('test', 'value', ('return_this',)),
            )
        cloud_jwt.create_jwt(jwt_config, 'deadbeef', 'GET', 'bucket', 'key')
        args, kwargs = encode.call_args
        assert args[0] == {'test': 'return_this'}

    @patch('pybossa.uploader.cloud_jwt.jwt.encode')
    def test_jwt_request(self, encode):
        jwt_config = (
                ('test_method', 'request', ('method',)),
            )
        cloud_jwt.create_jwt(jwt_config, 'deadbeef', 'OPTIONS', 'bucket', 'key')
        args, kwargs = encode.call_args
        assert args[0] == {'test_method': 'OPTIONS'}

    @patch('pybossa.uploader.cloud_jwt.jwt.encode')
    def test_jwt_path(self, encode):
        jwt_config = (
                ('test_path', 'path', ('/test',)),
            )
        cloud_jwt.create_jwt(jwt_config, 'deadbeef', 'OPTIONS', 'bucket', 'key')
        args, kwargs = encode.call_args
        assert args[0] == {'test_path': '/test/bucket/key'}

    @patch('pybossa.uploader.cloud_jwt.jwt.encode')
    @patch('pybossa.uploader.cloud_jwt.time.time')
    def test_jwt_timestamp(self, time, encode):
        time.return_value = 123456
        jwt_config = (
                ('test_timestamp', 'timestamp', (0,)),
            )
        cloud_jwt.create_jwt(jwt_config, 'deadbeef', 'OPTIONS', 'bucket', 'key')
        args, kwargs = encode.call_args
        assert args[0] == {'test_timestamp': 123456}

    @patch('pybossa.uploader.cloud_jwt.jwt.encode')
    @patch('pybossa.uploader.cloud_jwt.time.time')
    def test_jwt_timestamp_with_offset(self, time, encode):
        time.return_value = 123456
        jwt_config = (
                ('test_timestamp', 'timestamp', (50,)),
            )
        cloud_jwt.create_jwt(jwt_config, 'deadbeef', 'OPTIONS', 'bucket', 'key')
        args, kwargs = encode.call_args
        assert args[0] == {'test_timestamp': 123456 + 50}

    @patch('pybossa.uploader.cloud_jwt.jwt.encode')
    @patch('pybossa.uploader.cloud_jwt.time.time')
    def test_jwt_many(self, time, encode):
        time.return_value = 123456
        jwt_config = (
                ('test', 'value', ('return_this',)),
                ('test_method', 'request', ('method',)),
                ('test_timestamp', 'timestamp', (50,)),
            )
        cloud_jwt.create_jwt(jwt_config, 'deadbeef', 'PUT', 'bucket', 'key')
        args, kwargs = encode.call_args
        assert args[0] == {
            'test_timestamp': 123456 + 50,
            'test_method': 'PUT',
            'test': 'return_this'
        }
