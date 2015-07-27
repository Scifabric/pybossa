This folder contains the static and templates folders as a full theme for
PyBossa.

It also has the translations for PyBossa within the theme folder. To enable
multiple languages in your PyBossa installation, just make a simbolic link
to the translations folder in the theme:

cd ..
ln -s themes/the-theme/translations 

Then, PyBossa will read the translations and serve them properly.
