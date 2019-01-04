from pybossa import otp


def test_create_otp():
    user_email = 'test@test.com'
    secret = str(otp.generate_otp_secret(user_email)).encode('utf-8')
    assert otp.retrieve_user_otp_secret(user_email) == secret, ('', secret)


def test_get_otp_no_email():
    user_email = 'not@here.com'
    assert otp.retrieve_user_otp_secret(user_email) is None


def test_create_token():
    user_email = b'test@test.com'
    token = otp.generate_url_token(user_email)
    assert otp.retrieve_email_for_token(token) == user_email


def test_get_token_no_email():
    assert otp.retrieve_email_for_token('not@here.com') is None


def test_expire_token():
    user_email = 'test@test.com'
    token = otp.generate_url_token(user_email)
    otp.expire_token(token)
    assert otp.retrieve_email_for_token(token) is None
