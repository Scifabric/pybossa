# Update Project: {{blog['title']}} by {{blog['owner']['name']}} [1]
{{blog['body'] | striptags }}
***
[1]{{url_for('project.show_blogpost', short_name=blog.project.short_name, id=blog.id, _external=True)}}
***
***
[UNSUBSCRIBE]({{ url_for('account.update_profile', name=user_name, _external=True)}})
Powered by [PyBossa](http://pybossa.com)
Follow us: [Twitter](http://twitter.com/pybossa), [Google+](https://plus.google.com/115359083217638640334/posts)
