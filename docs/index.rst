*****
konch
*****

.. container:: release

   Release v\ |version|

.. container:: centered

   :doc:`changelog <changelog>` //
   `github <https://github.com/sloria/konch>`_ //
   `pypi <https://pypi.python.org/pypi/konch>`_ //
   `issues <https://github.com/sloria/konch/issues>`_

.. contents::
   :local:
   :depth: 1


Configure your Python shell
===========================

**konch** is a CLI and configuration utility for the Python shell, optimized for simplicity and productivity.

- **Automatically import** any object upon startup
- **Simple**, per-project configuration in a single file (it's just Python code)
- **No external dependencies**
- Uses **IPython**, **BPython**, or **ptpython** if available, and falls back to built-in interpreter
- Automatically load **IPython extensions**
- Can have multiple configurations per project using **named configs**

.. image:: https://zippy.gfycat.com/EachTerrificChupacabra.gif
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

Supports Python 3 (tested on 3.6 and 3.7). There are no external dependencies.

.. note::

   If you are using Python 2, ``konch<4.0`` will be installed with the
   above command.

Usage
=====

``$ konch``
-----------

runs the shell.

``$ konch allow [<config_file>]``
---------------------------------

authorizes a config file. **You MUST run this command before using a new config file**. This is a security mechanism to prevent execution of untrusted config files.

By default, the auth file is stored in ``~/.local/share/konch_auth``. You can change the location by setting the ``KONCH_AUTH_FILE`` environment variable.

``$ konch init``
----------------

creates a ``.konchrc`` file in your current directory.

``.konchrc`` is a Python file that calls the ``konch.config(config_dict)`` function.
See the `Configuration`_ section for a listing of options.

Here is an example ``.konchrc`` file that includes some functions from the `requests <https://docs.python-requests.org/en/latest/>`_ library in its context.

.. code-block:: python

    # .konchrc
    import konch
    import requests

    konch.config(
        {
            "context": {
                "httpget": requests.get,
                "httppost": requests.post,
                "httpput": requests.put,
                "httpdelete": requests.delete,
            },
            "banner": "A humanistic HTTP shell",
        }
    )

Now, when you run ``konch`` again:

.. image:: https://user-images.githubusercontent.com/2379650/50376317-8a6dbb00-05d9-11e9-8d42-983e40f2c264.gif
    :alt: konch with requests

.. seealso::

    For more examples, see the `example_rcfiles <https://github.com/sloria/konch/tree/master/example_rcfiles>`_ directory.

.. note::

    ``.konchrc`` files created with ``konch init`` are automatically authorized.

.. note::

    You can override the default file contents of ``.konchrc`` by creating a ``~/.konchrc.default`` file in your home directory.


``$ konch edit``
----------------

opens the current config file in your editor. Automatically authorizes the file when editing is finished.

Checks the ``KONCH_EDITOR``, ``VISUAL`` and ``EDITOR`` environment
variables (in that order) to determine which editor to use.


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
    konch.config({"context": [os, sys]})

    konch.named_config(
        "http", {"context": {"httpget": requests.get, "httppost": requests.post}}
    )

    konch.named_config(
        "flask", {"context": [flask.Flask, flask.url_for, flask.render_template]}
    )

To use the ``flask`` config, you would run:

.. code-block:: bash

    $ konch -n flask

You can also pass multiple names to ``named_config``:

.. code-block:: python

    # konch -n flask
    # OR
    # konch -n fl
    konch.named_config(
        ["flask", "fl"], {"context": [flask.Flask, flask.url_for, flask.render_template]}
    )

``$ konch -s <shell>``
----------------------

overrides the default shell. Choose between ``ipy``, ``bpy``, ``py``, ``ptpy``, ``ptipy``, or ``auto``.


``$ konch -f <file>``
---------------------

starts a session using ``<file>`` as its config file instead of the default ``.konchrc``.

``$ konch deny [<config_file>]``
--------------------------------

removes authorization for a config file.


Configuration
=============

- ``context``: A dictionary or list of objects that will be be available in your shell session. May also be a callable that returns a dictionary or list of objects.
- ``shell``: Default shell. May be ``'ipy'``, ``'bpy'``, ``'ptpy'``, ``'ptipy'``, ``'py'``, or ``'auto'`` (default). You can also pass a ``Shell`` class directly, such as  ``konch.IPythonShell``, ``konch.BPythonShell``, ``konch.PtPythonShell``, ``konch.PtIPythonShell``,  ``konch.PythonShell``, or ``konch.AutoShell``.
- ``banner``: Custom banner text.
- ``prompt``: The input prompt (not supported with BPython).
- ``output``: The output prompt (supported in IPython and PtIPython only).
- ``context_format``: Format to display ``context``. May be ``'full'``, ``'short'``, ``hide``, or a function that receives the context dictionary as input and returns a string.


Setup and Teardown Functions
============================

You can optionally define ``setup()`` and/or ``teardown()`` functions which will execute immediately before and after running the shell, respectively.

.. code-block:: python

    import os
    import shutil
    import konch


    def setup():
        os.mkdir("my_temp_dir")


    def teardown():
        shutil.rmtree("my_temp_dir")


    konch.config({"context": {"pjoin": os.path.join}})


IPython Extras
==============

``konch`` provides a few IPython-specific options.

Loading Extensions
------------------

The ``ipy_extensions`` option is used to automatically load IPython extensions at startup.

.. code-block:: python

    import konch

    konch.config(
        {
            # ...
            "shell": "ipython",
            "ipy_extensions": ["autoreload", "rpy2.ipython"],
        }
    )

Autoreload
----------

The ``ipy_autoreload`` option enables and initializes the IPython `autoreload <https://ipython.readthedocs.io/en/stable/config/extensions/autoreload.html>`_ extension at startup.

.. code-block:: python

    import konch

    konch.config(
        {
            # ...
            "shell": "ipython",
            # Automatically reload modules
            "ipy_autoreload": True,
        }
    )

This is equivalent to running: ::

    % load_ext autoreload
    % autoreload 2

Colors
------

The ``ipy_colors`` and ``ipy_highlighting_style`` options are used to configure colors in the IPython shell. ``ipy_colors`` sets the color of tracebacks and object info (the output of e.g. ``zip?``). ``ipy_highlighting_style`` sets colors for syntax highlighting.

.. code-block:: python

    import konch

    konch.config(
        {
            # ...
            "shell": "ipython",
            # 'linux' is optimized for dark terminal backgrounds
            "ipy_colors": "linux",
            "ipy_highlighting_style": "monokai",
        }
    )


See the IPython docs for more information and valid values for these options: https://ipython.readthedocs.io/en/stable/config/details.html#terminal-colors

ptpython support
================

``konch`` supports both `ptpython <https://github.com/jonathanslenders/ptpython>`_ and ptipython. If either is installed in your current environment, running ``konch`` will run the available shell.

``konch`` provides a few ptpython-specific options.

To use ptpython's vi-style bindings, set the ``ptpy_vi_mode`` option in your ``.konchrc``. You can also use the ``ipy_extensions`` option to load IPython extensions at startup (must be using ``ptipython``).

.. code-block:: python

    import konch

    konch.config(
        {
            # ...
            "shell": "ptipython",
            "ptpy_vi_mode": True,
            "ipy_extensions": ["autoreload"],
        }
    )


Using ``.konchrc.local``
========================

If you're distributing your ``.konchrc`` in a git repo, you
may want to allow collaborators to extend your configuration in an
unversioned ``.konchrc.local`` file.

First, add ``.konchrc.local`` to ``.gitignore``.

.. code-block:: bash

   # .gitignore

   .konchrc.local


Then add the following to your ``.konchrc``:

.. code-block:: python

    # .konchrc

    from pathlib import Path

    # konch.config(...)

    if Path(".konchrc.local").exists():
        konch.use_file(".konchrc.local", trust=True)


.. note::

    The ``context`` in ``.konchrc.local`` will be merged
    with the context in ``.konchrc``.

.. note::

   Passing ``trust=True`` allows ``.konchrc.local`` to be
   edited without requiring approval.
   **This is safe if (and only if) .konchrc.local is not
   added to source control.**


Programmatic Usage
==================

Want to use konch within a Python script? konch exposes many of its high-level functions.

.. code-block:: python

    import konch
    from mypackage import cheese

    # Start the shell
    konch.start(context={"cheese": cheese}, shell=konch.AutoShell)

To use a config file:

.. code-block:: python

    import konch

    konch.use_file("~/path/to/.mykonchrc")
    konch.start()

Get command-line arguments using ``konch.parse_args()``. ``konch`` uses `docopt`_ for arguments parsing.



.. code-block:: python

    import konch
    from myapp import app, db

    args = konch.parse_args()
    if args["--name"] == "db":
        # ...expensive database setup...
        konch.start(context={"db": db, "app": app})
    else:
        konch.start(context={"app": app})

.. _docopt: http://docopt.org

You can also use shell objects directly:

.. code-block:: python

    import konch

    my_shell = konch.AutoShell(context={"foo": 42}, banner="My foo shell")
    my_shell.start()


Integrating with setuptools / ``python setup.py shell``
=======================================================

You can integrate konch into your setuptools-based project using
the following ``Command`` class.

.. code-block:: python

    # setup.py
    import shlex
    from setuptools import Command


    class Shell(Command):
        user_options = [("args=", "a", "Arguments to pass to konch")]

        def initialize_options(self):
            self.args = ""

        def finalize_options(self):
            pass

        def run(self):
            import konch

            konch.main(shlex.split(self.args))


    setup(
        # ...,
        cmdclass={"shell": Shell}
    )


You can now run:

.. code-block:: bash

   $ python setup.py shell


You can also pass a string of arguments:


.. code-block:: bash
 
   $ python setup.py shell -a "--shell ipy"

..

    "Praise the Magic Conch!"

Project Info
============


.. toctree::
   :maxdepth: 1

   license
   changelog
