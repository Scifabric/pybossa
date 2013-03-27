===================
Translating PyBossa
===================

PyBossa supports i18n locales, so you can translate the **User Interface** to
any language. By default PyBossa comes with two different languages: English
and Spanish.

If you want to translate PyBossa to your own language, lets say French, all you have to do is
create a translation file with this command:

.. code-block:: bash

    $ pybabel init -i messages.pot -d translations -l fr

Then, open the file **translations/fr/LC_MESSAGES/messages.po** with any text
editor and translate the English strings to French. For example, if you get
this string:

.. code-block::

    #: templates/_gcs_form.html:6 templates/admin/users.html:20
    msgid "Search"
    msgstr ""


All you have to do is to translate **Search** to its equivalent in French
**Rechercher** and type in the msgstr section:

.. code-block::

    #: templates/_gcs_form.html:6 templates/admin/users.html:20
    msgid "Search"
    msgstr "Rechercher"

Once you have translated all the strings, all you have to do is compile the
translation with this command:

.. code-block::

    $ pybabel compile -d translations

And now enable the new locale in the server local_settings.py file. Check for
the LOCALES config variable and add your locale.

Adding new strings to the translation
=====================================

From time to time, the PyBossa framework will add new strings to translate. In
order to add the new strings (or update previous ones) you only have to follow
this step:

.. code-block:: bash

    $ pybabel update -i translations/messages.pot -d translations

This will update your French translation file (messages.po) and will try to
guess some of the translations for saving you time. While this feature is
really good, somtimes the translation is not good enough, so you will get the
word: **fuzzy** on top of the translation. Check all the **fuzzy** translations
and fix them. When you are done, remove the line with the word **fuzzy** and
re-compile the translations.

Contributing your translation to the upstream repository
========================================================

We would love to support more and more languages by default, so if you have
done a translation and you would like that we include it in the default
package, send us a github pull request with your translations or if you prefer
by e-mail to info@pybossa.com

We will be very happy to add your contributions to the system.
