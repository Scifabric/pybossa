Repo for a Bootstrap based sphinx theme with lots of customizability (e.g.
google analytics, logo etc).

Theme Options
=============

* logo\_icon: logo icon url (can be local in \_static) to use in top bar (in
  addition to title). Will be rendered with a height of 25px.
* git\_repo: git(hub) repository link for the fork me badge. Example:
  `https://github.com/okfn/sphinx-theme-okfn`

Configuring the sidebar:

* Use the standard sphinx sidebars setup: http://sphinx.pocoo.org/config.html#confval-html\_sidebars

  * E.g. to have the global ToC there just add globaltoc.html to the list. To
    have local table of contents (for current page) at localtoc.html to the
    list.

Configuring the Footer
----------------------

Override the footer.html template.


Configuring the Top Bar
-----------------------

You can add navigation links (and other material) to the top bar by overriding the navbar-nav.html template. This material will fit into the bootstrap topbar after the main brand link on the left. An example navbar-nav would be:

    <ul class="nav">
      <li><a href="">my link</a></li>
    </ul>


How to Use
==========

Imagine you have a sphinx project with layout like:

    source
      conf.py
    {other-dirs ...}  

You would do:

    git submodule add git://github.com/okfn/sphinx-theme-okfn.git source/_themes/sphinx-theme-okfn
    # then commit ...
    git commit -m "Adding submodule for sphinx-theme-okfn"

Then in `conf.py` you would config like:

<pre>
sys.path.append(os.path.abspath('_themes'))
html_theme_path = ['_themes']
html_theme = 'sphinx-theme-okfn'
html_theme_options = {
        'logo_icon': ...
        'google_analytics_id': ...
    }
</pre>

**Note**: If you use the theme as it is, a broken search box will be rendered
in the left sidebar. In order to fix it, customize the items rendered in the
sidebar:

<pre>
    html_sidebars = {
        '**': ['globaltoc.html', 'localtoc.html', 'relations.html']
    }
</pre>

License
=======

Copyright (c) 2012 Open Knowledge Foundation

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.

