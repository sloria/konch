=====
konch
=====

Tired of importing things whenever you start your Python shell? **konch can help.**

.. code-block:: bash

    $ pip install konch
    $ konch init
    Initialized konch. Edit .konchrc to your needs and run `konch` to start an interactive session.
    $ konch

- Automatically import any object upon startup
- Per-project configuration
- Compatible with IPython and BPython (automatically falls back to built-in interpreter)
- No hard dependencies

Screencast
----------

.. image:: https://dl.dropboxusercontent.com/u/1693233/github/Screenshot%202014-03-14%2001.21.31.png
  :target: http://showterm.io/12e3b0f27a6a77b7e47e0#fast


Install/Upgrade
---------------

.. code-block:: bash

    $ pip install -U konch


Usage
-----

.. code-block:: bash

    $ konch init

creates a ``.konchrc`` file in your current directory.

``.konchrc`` is just a regular Python file that calls the ``konch.config(config_dict)`` function.

You can pass any of the following options:

- ``context``: A list or dictionary of objects that will be immediately available to you in your shell session.
- ``shell``: Default shell to use. May be ``konch.IPythonShell``, ``konch.BPythonShell``, ``konch.PythonShell``, or ``konch.AutoShell`` (default).
- ``banner``: Custom banner text to show.

Here is an example ``.konchrc`` file that includes some functions from the `requests <http://docs.python-requests.org/en/latest/>`_ library in its context.

.. code-block:: python

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

For more examples, see the `example_rcfiles <https://github.com/sloria/konch/tree/master/example_rcfiles>`_ directory.

For more info on available command-line options, run ``konch --help``.


Requirements
------------

- Python 2 or 3 (tested on 2.6, 2.7, 3.2, 3.3)

License
-------

MIT licensed. See the bundled `LICENSE <https://github.com/sloria/konch/blob/master/LICENSE>`_ file for more details.
