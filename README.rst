==================================
dpaste - code pastebin application
==================================

Originally inspired by dpaste.com this application adds the ability to:

- See the differences between snippets
- A history of snippets as a tree
- See your latest 25 snippets (admin setting)
- A huge bunch of syntax highlighters (lexers)
- User defined settings to change the font-family as well as font-sizes
- Nice colors 
- Multilangual interface
- per-user defined expiration of snippets

milki fork features:

- Snippets are materialized as files within a git repo
  - Snippet tree represents a branch
- Snippets represent irc logs
  - Only one log file per branch
  - Each snippet represents a version of the log file in that branch

Installation:
=============

1. Add ``dpaste`` to your pythonpath.
2. Add ``dpaste`` to your ``INSTALLED_APPS`` in your django project settings.
3. Add this line to your urlsconf::

    (r'^mypaste/', include('dpaste.urls')),

Requirements:
=============

- `django-mptt`_ for the nested-set history tree
- Pygments_ for syntax highlighting 
- dulwich_ for git backend

.. _`django-mptt`: http://code.google.com/p/django-mptt/
.. _Pygments: http://pygments.org/
.. _dulwich: http://www.samba.org/~jelmer/dulwich/

Latest version:
===============

The primary repository is located on Github: http://github.com/bartTC/django-paste/
milki's fork is located: https://github.com/milki/django-paste
