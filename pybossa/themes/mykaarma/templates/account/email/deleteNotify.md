Hi, {{ user['fullname']}}!

We notice you haven’t been around {{config.BRAND}} for more than five months. We would like to encourage you to visit us again and continue collaborating with us. If you don't contribute in the next month to a project, your account will be
deleted from our systems.

Regards,

{{ config.BRAND }} Team

***
[UNSUBSCRIBE]({{ url_for('account.update_profile', name=user['name'], _external=True)}})
Powered by [PyBossa](http://pybossa.com)
Follow us: [Twitter](http://twitter.com/pybossa), [Google+](https://plus.google.com/115359083217638640334/posts)
