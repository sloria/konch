*****
konch
*****

`github <http://github.com/sloria/konch>`_ //
`pypi <http://pypi.python.org/pypi/konch>`_ //
`issues <http://github.com/sloria/konch/issues>`_

The customizable Python shell
=============================

- **Automatically import** any object upon startup
- **Simple** configuration syntax (it's just Python code)
- Written in **pure Python**
- **No hard dependencies**
- Uses **IPython** and **BPython** if available, and falls back to built-in interpreter
- Can have multiple configurations per project using **named configs**

.. image:: https://dl.dropboxusercontent.com/u/1693233/github/konchdemo-optim.gif
    :alt: Demo

Install/Upgrade
===============

.. code-block:: bash

    $ pip install -U konch

Supports Python 2 and 3 (tested on 2.6, 2.7, 3.2, 3.3). There are no other dependencies.

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
- ``shell``: Default shell. May be ``konch.IPythonShell``, ``konch.BPythonShell``, ``konch.PythonShell``, or ``konch.AutoShell`` (default).
- ``banner``: Custom banner text.

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

.. seealso::

    For more examples, see the `example_rcfiles <https://github.com/sloria/konch/tree/master/example_rcfiles>`_ directory.



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


..


    "Praise the Magic Conch!"


.. toctree::
   :maxdepth: 1

   license
   changelog





