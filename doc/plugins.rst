====================================
Writing plugins for a PyBossa server
====================================

PyBossa has a plugin system that allows you to write your own custom features
and add them to a running PyBossa server without the need of touching the server
code. For instance, you could create a new endpoint for an admin dashboard (with
new views, templates, etc.) or build a new scheduler like in `this example <https://github.com/PyBossa/random-scheduler>`_.

The PyBossa plugin system is powered by `Flask-plugins`_

To create a plugin, you will have to make a folder with the name of your plugin
and add it to the plugins folder in your PyBossa server. If you have the PyBossa
code in a directory called pybossa, then the plugins folder will be pybossa/pybossa/plugins.

The least you need to include in that folder is the following::

    your_plugin_folder
    |-- info.json
    |-- __init__.py

__init__.py will have to contain your plugin class, that needs to inherit from
flask.ext.plugins.Plugin. On the other hand, info.json needs to follow the schema::

    {
        "identifier": "identifier",
        "name": "PluginClass",
        "author": "you@yourdomain.com",
        "license": "AGPLv3",
        "description": "whatever",
        "version": "0.0.1"
    }

You could also create a more sofisticated plugin, including your own templates,
models, forms... everything you need::

    your_plugin_folder
    |-- info.json                Contains the Plugin's metadata
    |-- license.txt              The full license text of your plugin
    |-- __init__.py              The plugin's main class is located here
    |-- views.py
    |-- models.py
    |-- forms.py
    |-- static
    |   |-- style.css
    |-- templates
        |-- myplugin.html

For more information and examples, please refer to the Flask-plugins documentation_.

.. _`Flask-plugins`: https://github.com/sh4nks/flask-plugins
.. _documentation: http://flask-plugins.readthedocs.org/en/latest/
