*********
Changelog
*********

3.0.0 (unreleased)
------------------

Features:

- Config files must be approved before executing them.
  Use ``konch allow`` to authorize a config file. This is a security mechanism to prevent
  executing untrusted Python code `#47 <https://github.com/sloria/konch/issues/47>`_.
  Thanks `@hartwork <https://github.com/hartwork>`_ for the suggestion.
- Allow customizing the editor to use for ``konch edit`` via the
  ``KONCH_EDITOR`` environment variable.
- ``konch init`` only adds the encoding pragma (``# -*- coding: utf-8 -*-\n``) on Python 2.
- Raise error when an invalid ``--name`` is passed.

Bug fixes:

- Address a ``DeprecationWarning`` about importing from ``collections.abc`` on Python 3.7.

2.5.0 (2018-11-04)
------------------

- Update dev environment.
- Python 3.4 is no longer officially supported.
- Tested on Python 3.7.

2.4.0 (2017-04-29)
------------------

Features:

- Add basic tab-completion to plain Python shell.

2.3.0 (2016-12-23)
------------------

Features:

- Allow ``context`` to be a callable.
- Multiple names may be passed to ``named_config``.

2.2.1 (2016-12-19)
------------------

Bug fixes:

- Fix error raised when some options are passed to ``konch.named_config``.

2.2.0 (2016-07-21)
------------------

Features:

- Add ``ipy_colors`` and ``ipy_highlighting_style`` options for customizing IPython terminal colors.

2.1.0 (2016-07-18)
------------------

Features:

- Compatibility with IPython>=5.0.0.

Support:

- Update tasks.py for compatibility with invoke>=0.13.0.

2.0.0 (2016-06-01)
------------------

Features:

- Customizable context formatting via the ``context_format`` option.
- More CONCHES!

Deprecations/Removals:

- Remove ``hide_context`` option. Use the ``context_format`` option instead.
- Drop support for Python<=2.6 and <=3.3.

Bug fixes:

- Fix bug in checking availability of PtIPython.
- Fix bug in passing shell subclass as ``shell`` argument to ``konch.start``.

1.1.2 (2016-05-24)
------------------

- ``ShellNotAvailableErrors`` no longer pollute tracebacks when using the ``AutoShell``.

1.1.1 (2015-09-27)
------------------

- Remove deprecated import of IPython.config.

1.1.0 (2015-06-21)
------------------

- Add ptpython support.

1.0.0 (2015-02-08)
------------------

- Add support for ``setup`` and ``teardown`` functions in ``.konchrc`` files.
- If ``~/.konchrc.default`` exists, use that file as the template for new ``.konchrc`` files created with ``konch init``.
- Add ``ipy_extensions`` and ``ipy_autoreload`` options.
- Make sure that vim opens .konchrc files in Python mode.
- Drop Python 3.2 support.

0.4.2 (2014-07-12)
------------------

- "shell" option in .konchrc can be a string: either 'bpy', 'ipy', 'py', or 'auto'.
- Fix error in "konch edit".

0.4.1 (2014-06-23)
------------------

- Fix bug that caused konch to hang if no .konchrc file can be found.

0.4.0 (2014-06-10)
------------------

- Add ``edit`` command for editing .konchrc file.
- Properly output error messages to stderr.
- Tested on Python 3.4.

0.3.4 (2014-04-06)
------------------

- Fix bug that raised `SyntaxError` when executing konch on Windows.

0.3.3 (2014-03-27)
------------------

- Fix bug in resolve_path that caused infinite loop if config file not found.
- Fix bug with initializing konch in home directory.
- Add ``hide_context`` option.

0.3.2 (2014-03-18)
------------------

- Some changes to make it easier to use konch programatically.
- ``konch.start()`` can be called with no arguments.
- Expose docopt argument parsing via ``konch.parse_args()``.


0.3.1 (2014-03-17)
------------------

- Doesn't change current working directory.
- Less magicks.
- Tested on Python 3.4.


0.3.0 (2014-03-16)
------------------

- Smarter path resolution. konch will search parent directories until it finds a .konchrc file to use.
- Make prompt configurable on IPython and built-in shell. Output template is also supported on IPython.
- *Backwards-incompatible*: Remove support for old (<=0.10.x--released 3 years ago!) versions of IPython.

0.2.0 (2014-03-15)
------------------

- Fix bug with importing modules and packages in the current working directory.
- Introducing *named configs*.

0.1.0 (2014-03-14)
------------------

- First release to PyPI.
