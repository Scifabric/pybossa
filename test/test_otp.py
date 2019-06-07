import json
from default import with_context
from pybossa import otp

class JSONObject:
    def __init__( self, dict ):
        vars(self).update(dict)

@with_context
def test_create_otp():
    user_email = 'test@test.com'
    secret = str(otp.generate_otp_secret(user_email))
    assert otp.retrieve_user_otp_secret(user_email) == secret, ('', secret)


@with_context
def test_get_otp_no_email():
    user_email = 'not@here.com'
    assert otp.retrieve_user_otp_secret(user_email) is None


@with_context
def test_create_token():
    user_email = 'test@test.com'
    token = otp.generate_url_token(user_email)
    assert otp.retrieve_email_for_token(token) == user_email


@with_context
def test_get_token_no_email():
    assert otp.retrieve_email_for_token('not@here.com') is None


@with_context
def test_expire_token():
    user_email = 'test@test.com'
    token = otp.generate_url_token(user_email)
    otp.expire_token(token)
    assert otp.retrieve_email_for_token(token) is None


@with_context
def test_otp_enabled():
    user_email = 'test@test.com'
    config = json.loads('{ "ENABLE_TWO_FACTOR_AUTH": true }', object_hook=JSONObject)

    assert otp.is_enabled(user_email, config) is True

@with_context
def test_otp_disabled():
    user_email = 'test@test.com'
    config = json.loads('{ "ENABLE_TWO_FACTOR_AUTH": false }', object_hook=JSONObject)

    assert otp.is_enabled(user_email, config) is False

@with_context
def test_otp_enabled_user_bypass():
    user_email = 'test@test.com'
    config = json.loads('{ "ENABLE_TWO_FACTOR_AUTH": true, "BYPASS_TWO_FACTOR_AUTH": ["test@test.com"] }', object_hook=JSONObject)

    assert otp.is_enabled(user_email, config) is False

@with_context
def test_otp_disabled_user_bypass():
    user_email = 'test@test.com'
    config = json.loads('{ "ENABLE_TWO_FACTOR_AUTH": false, "BYPASS_TWO_FACTOR_AUTH": ["test@test.com"] }', object_hook=JSONObject)

    assert otp.is_enabled(user_email, config) is False

@with_context
def test_otp_enabled_user_no_bypass():
    user_email = 'test@test.com'
    config = json.loads('{ "ENABLE_TWO_FACTOR_AUTH": true, "BYPASS_TWO_FACTOR_AUTH": ["test2@test.com"] }', object_hook=JSONObject)

    assert otp.is_enabled(user_email, config) is True

@with_context
def test_otp_disabled_user_no_bypass():
    user_email = 'test@test.com'
    config = json.loads('{ "ENABLE_TWO_FACTOR_AUTH": false, "BYPASS_TWO_FACTOR_AUTH": ["test2@test.com"] }', object_hook=JSONObject)

    assert otp.is_enabled(user_email, config) is False
