Hi, {{ user['fullname']}}!

We notice you haven’t been around {{config.BRAND}} for more than three months. We would like to encourage you to visit us again and continue collaborating with us. We hope not to bother you with this email- we’re just trying to make you not forget about us.

In any case, thank you for your contribution so far.

Cheers!

{{ config.BRAND }} Team

***
[UNSUBSCRIBE]({{ url_for('account.update_profile', name=user['name'], _external=True)}})
Powered by [PyBossa](http://pybossa.com)
Follow us: [Twitter](http://twitter.com/pybossa), [Google+](https://plus.google.com/115359083217638640334/posts)
