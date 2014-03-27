*********
Changelog
*********

0.3.3 (unreleased)
------------------

- Fix bug in resolve_path that caused infinite loop if config file not found.
- Fix bug with initializing konch in home directory.

0.3.2 (2014-03-18)
------------------

- Some changes to make it easier to use konch programatically.
- ``konch.start()`` can be called with no arguments.
- Expose docopt argument parsing via ``knoch.parse_args()``.


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
