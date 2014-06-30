*****
konch
*****

`github <http://github.com/sloria/konch>`_ //
`pypi <http://pypi.python.org/pypi/konch>`_ //
`issues <http://github.com/sloria/konch/issues>`_


Configures your Python shell
============================

**konch** is a CLI and configuration utility for the Python shell, optimized for simplicity and productivity.

- **Automatically import** any object upon startup
- **Simple**, per-project configuration in a single file (it's just Python code)
- **No dependencies**
- Uses **IPython** and **BPython** if available, and falls back to built-in interpreter
- Can have multiple configurations per project using **named configs**

.. image:: https://dl.dropboxusercontent.com/u/1693233/github/konch-030-demo-optim.gif
    :alt: Demo


Example Use Cases
-----------------

- If you're building a web app, you can have all your models in your shell namespace without having to import them individually. You can also run any necessary database or app setup.
- If you're building a Python package, you can automatically import all of its modules.
- In a live demo, skip the imports.
- Immediately have test objects to work with in interactive sessions.


Install/Upgrade
===============

.. code-block:: bash

    $ pip install -U konch

Supports Python 2 and 3 (tested on 2.6, 2.7, 3.2, 3.3, 3.4). There are no other dependencies.

Usage
=====

``$ konch``
-----------

runs the shell.

``$ konch init``
----------------

creates a ``.konchrc`` file in your current directory.

``.konchrc`` is just a Python file that calls the ``konch.config(config_dict)`` function.

You can pass any of the following options:

- ``context``: A dictionary or list of objects that will be immediately available to you in your shell session.
- ``shell``: Default shell. May be ``'ipy'``, ``'bpy'``, ``'py'``, or ``'auto'`` (default). You can also pass a ``Shell`` class directly, such as  ``konch.IPythonShell``, ``konch.BPythonShell``, ``konch.PythonShell``, or ``konch.AutoShell``.
- ``banner``: Custom banner text.
- ``prompt``: The input prompt (not supported with BPython).
- ``hide_context``: If ``True``, don't show the context variables in the banner. Defaults to ``False``.

Here is an example ``.konchrc`` file that includes some functions from the `requests <http://docs.python-requests.org/en/latest/>`_ library in its context.

.. code-block:: python

    # .konchrc
    import konch
    import requests

    konch.config({
        'context': {
            'httpget': requests.get,
            'httppost': requests.post,
            'httpput': requests.put,
            'httpdelete': requests.delete
        },
        'banner': 'A humanistic HTTP shell'
    })

Now, when you run ``konch`` again:

.. image:: https://dl.dropboxusercontent.com/u/1693233/github/konch-requests.gif
    :alt: konch with requests

.. seealso::

    For more examples, see the `example_rcfiles <https://github.com/sloria/konch/tree/master/example_rcfiles>`_ directory.


``$ konch edit``
----------------

opens the current config file in your editor.


``$ konch -n <name>``
---------------------

selects a *named config*.

Named configs allow you to have multiple configurations in the same ``.konchrc``
file.

.. code-block:: python

    # .konchrc
    import konch
    import os
    import sys
    import requests
    import flask

    # The default config
    konch.config({
        'context': [os, sys]
    })

    konch.named_config('http', {
        'context': {
            'httpget': requests.get,
            'httppost': requests.post
        }
    })

    konch.named_config('flask', {
        'context': {
            'request': flask.request,
            'Flask': flask.Flask,
            'url_for': flask.url_for
        }
    })

To use the ``flask`` config, you would run:

.. code-block:: bash

    $ konch -n flask

``$ konch -s <shell>``
----------------------

overrides the default shell. Choose between ``ipy``, ``bpy``, or ``py``.


``$ konch -f <file>``
---------------------

starts a session using ``<file>`` as its config file instead of the default ``.konchrc``.


Programmatic Usage
==================

Want to use konch within a Python script? konch exposes many of its high-level functions.

.. code-block:: python

    import konch
    from mypackage import cheese

    # Start the shell
    konch.start(
        context={
            'cheese': cheese
        },
        shell=konch.AutoShell
    )

To use a config file:

.. code-block:: python

    import konch

    konch.use_file('~/path/to/.mykonchrc')
    konch.start()

Get command-line arguments using ``konch.parse_args()``. ``konch`` uses `docopt`_ for arguments parsing.



.. code-block:: python

    import konch
    from myapp import app, db

    args = konch.parse_args()
    if args['--name'] == 'db':
        # ...expensive database setup...
        konch.start(context={
            'db': db,
            'app': app
        })
    else:
        konch.start(context={
            'app': app
        })

.. _docopt: http://docopt.org

You can also use shell objects directly:

.. code-block:: python

    import konch

    my_shell = konch.AutoShell(context={'foo': 42}, banner='My foo shell')
    my_shell.start()

..

    "Praise the Magic Conch!"


.. toctree::
   :maxdepth: 1

   license
   changelog





