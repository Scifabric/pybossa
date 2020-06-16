Hi, {{ user['fullname'] }}!

We notice you signed up for {{config.BRAND}} some time ago, but never contributed. We would like to encourage you to visit our project again and start collaborating with us. We hope not to bother you with this email- we’re just trying to make you give us a hand!

Cheers!

{{ config.BRAND }} Team

***
[UNSUBSCRIBE]({{ url_for('account.update_profile', name=user['name'], _external=True)}})
Powered by [PyBossa](http://pybossa.com)
Follow us: [Twitter](http://twitter.com/pybossa), [Google+](https://plus.google.com/115359083217638640334/posts)
