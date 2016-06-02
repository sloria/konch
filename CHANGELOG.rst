*********
Changelog
*********

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
