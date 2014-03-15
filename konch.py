#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''konch: Customizes your Python shell.

Usage:
  konch
  konch init
  konch init [<config_file>] [-d]
  konch [--name=<name>] [-d]
  konch [--name=<name>] [--file=<file>] [--shell=<shell_name>] [-d]

Options:
  -h --help                  Show this screen.
  -v --version               Show version.
  init                       Creates a starter .konchrc file.
  -s --shell=<shell_name>    Shell to use. Can be either "ipy" (IPython),
                              "bpy" (BPython), or "py" (built-in Python shell),
                               or "auto" (try to use IPython or Bpython and
                               fallback to built-in shell).
  -n --name=<name>           Named config to use.
  -f --file=<file>           File path of konch config file to execute. If not provided,
                               konch will use the .konchrc file in the current
                               directory.
  -d --debug                 Enable debugging/verbose mode.
'''

from __future__ import unicode_literals, print_function
import logging
import os
import sys
import code
import warnings
import random

from docopt import docopt

__version__ = '0.1.0'
__author__ = 'Steven Loria'
__license__ = 'MIT'

logger = logging.getLogger(__name__)

BANNER_TEMPLATE = """{version}

{text}
"""

CONTEXT_TEMPLATE = """
Context:
{context}
"""

DEFAULT_BANNER_TEXT = 'This is your konch shell. Happy hacking.'

DEFAULT_CONFIG_FILE = '.konchrc'

INIT_TEMPLATE = '''# -*- coding: utf-8 -*-
import konch

# TODO: Edit me
context = {
    'speak': konch.speak
}

# Available options: 'context', 'banner', 'shell'
konch.config({
    'context': context,
})
'''


def execute_file(fname, globals_=None, locals_=None):
    """Executes code in a file. Python 2/3-compatible."""
    exec(compile(open(fname, "rb").read(), fname, 'exec'), globals_, locals_)


def format_context(context):
    """Output the a context dictionary as a string."""
    if context is None:
        return ''
    line_format = '{name}: {obj!r}'
    return '\n'.join([
        line_format.format(name=name, obj=obj)
        for name, obj in context.items()
    ])


def make_banner(text=None, context=None):
    """Generates a full banner with version info, the given text, and a
    formatted list of context variables.
    """
    banner_text = text or DEFAULT_BANNER_TEXT
    out = BANNER_TEMPLATE.format(version=sys.version, text=banner_text)
    if context:
        out += CONTEXT_TEMPLATE.format(context=format_context(context))
    return out

def context_list2dict(context_list):
    """Converts a list of objects (functions, classes, or modules) to a
    dictionary mapping the object names to the objects.
    """
    return dict(
        (obj.__name__, obj) for obj in context_list
    )


class Shell(object):
    """Base shell class.

    :param dict context: Dictionary that defines what variables will be
        available when the shell is run.
    :param str banner: Banner text that appears on startup.
    """

    def __init__(self, context, banner=DEFAULT_BANNER_TEXT):
        self.context = context
        self.banner = make_banner(banner, context)

    def start(self):
        raise NotImplementedError


class PythonShell(Shell):
    """The built-in Python shell."""

    def start(self):
        code.interact(self.banner, local=self.context)
        return None


class IPythonShell(Shell):
    """The IPython shell."""

    def start(self):
        try:  # Backwards compatibility
            from IPython.Shell import IPShellEmbed
            ipshell = IPShellEmbed(banner=self.banner)
            ipshell(global_ns={}, local_ns=self.context)
        except ImportError:
            try:
                from IPython import embed
                embed(banner1=self.banner, user_ns=self.context)
            except ImportError:
                raise ShellNotAvailableError('IPython shell not available.')
        return None


class BPythonShell(Shell):
    """The BPython shell."""

    def start(self):
        try:
            from bpython import embed
            embed(banner=self.banner, locals_=self.context)
        except ImportError:
            raise ShellNotAvailableError('BPython shell not available.')
        return None


class AutoShell(Shell):
    """Shell that runs IPython or BPython if available. Falls back to built-in
    Python shell.
    """

    def __init__(self, context, banner=DEFAULT_BANNER_TEXT):
        self.context = context
        self.banner = banner

    def start(self):
        try:
            return IPythonShell(self.context, self.banner).start()
        except ShellNotAvailableError:
            try:
                return BPythonShell(self.context, self.banner).start()
            except ShellNotAvailableError:
                return PythonShell(self.context, self.banner).start()
        return None


class KonchError(Exception):
    pass


class ShellNotAvailableError(KonchError):
    pass

SHELL_MAP = {
    'ipy': IPythonShell, 'ipython': IPythonShell,
    'bpy': BPythonShell, 'bpython': BPythonShell,
    'py': PythonShell, 'python': PythonShell,
    'auto': AutoShell,
}


CONCHES = [
    ('"My conch told me to come save you guys."\n'
    '"Hooray for the magic conches!"'),
    '"All hail the Magic Conch!"',
    '"Hooray for the magic conches!"',
    '"Uh, hello there. Magic Conch, I was wondering... '
    'should I have the spaghetti or the turkey?"',
    '"This copyrighted conch is the cornerstone of our organization."',
    '"Praise the Magic Conch!"',
    '"the conch exploded into a thousand white fragments and ceased to exist."',
    '"S\'right. It\'s a shell!"',
    '"Ralph felt a kind of affectionate reverence for the conch"',
    '"Conch! Conch!"',
    '"That’s why you got the conch out of the water"',
    '"the summons of the conch"',
    '"Whoever holds the conch gets to speak."',
    '"They’ll come when they hear us—"',
    '"We gotta drop the load!"',
    '"Dude, we\'re falling right out the sky!!"',
    ('"Oh, Magic Conch Shell, what do we need to do to get out of the Kelp Forest?"\n'
        '"Nothing."'),
    '"The shell knows all!"',
    '"we must never question the wisdom of the Magic Conch."',
    '"The Magic Conch! A club member!"'
]


def speak():
    return random.choice(CONCHES)


class Config(dict):
    """A dict-like config object. Behaves like a normal dict except that
    the ``context`` will always be converted from a list to a dict.
    """

    def __init__(self, context=None, banner=None, shell=AutoShell):
        ctx = Config.transform_val(context) or {}
        super(Config, self).__init__(context=ctx, banner=banner, shell=shell)

    def __setitem__(self, key, value):
        val = Config.transform_val(value)
        super(Config, self).__setitem__(key, val)

    @staticmethod
    def transform_val(val):
        if isinstance(val, (list, tuple)):
            return context_list2dict(val)
        return val

    def update(self, d):
        for key in d.keys():
            self[key] = d[key]

# cfg and config_registry are global variables that may be mutated by a
# .konchrc file
cfg = Config()
config_registry = {
    'default': cfg
}


def start(context, banner=None, shell=AutoShell):
    """Start up the konch shell with a given context."""
    logger.debug('Using shell...')
    logger.debug(shell)
    if banner is None:
        banner = speak()
    shell(context, banner).start()


def config(config_dict):
    """Configures the konch shell. This function should be called in your
    .konchrc file.

    :param dict config_dict: Dict that may contain 'context', 'banner', and/or
        'shell' (default shell class to use).
    """
    global cfg
    cfg.update(config_dict)
    return cfg


def named_config(name, config_dict):
    global config_registry
    config_registry[name] = Config(**config_dict)


def reset_config():
    global cfg
    cfg = Config()
    return cfg


def get_file_directory(filename):
    return os.path.dirname(os.path.abspath(filename))


def __ensure_directory_in_path(filename):
    directory = get_file_directory(filename)
    if directory not in sys.path:
        logger.debug('Adding {0} to sys.path'.format(directory))
        sys.path.insert(0, directory)


def use_file(filename):
    # First update cfg by executing the config file
    config_file = filename or DEFAULT_CONFIG_FILE
    if os.path.exists(config_file):
        logger.info('Using {0}'.format(config_file))
        # Ensure that relative imports are possible
        __ensure_directory_in_path(config_file)
        execute_file(config_file)
    else:
        warnings.warn('"{0}" not found.'.format(config_file))
    return cfg


def init_config(config_file=None):
    if not os.path.exists(config_file):
        with open(config_file, 'w') as fp:
            fp.write(INIT_TEMPLATE)
        print('Initialized konch. Edit {0} to your needs and run `konch` '
                'to start an interactive session.'
                .format(config_file))
        sys.exit(0)
    else:
        print('{0} already exists in this directory.'
                .format(config_file))
        sys.exit(1)


def main():
    """Main entry point for the konch CLI."""
    global cfg
    args = docopt(__doc__, version=__version__)
    if args['--debug']:
        logging.basicConfig(
            format='%(levelname)s %(filename)s: %(message)s',
            level=logging.DEBUG)
    logger.debug(args)

    if args['init']:
        config_file = args['<config_file>'] or DEFAULT_CONFIG_FILE
        init_config(config_file)
    use_file(args['--file'])

    if args['--name']:
        config = config_registry.get(args['--name'], cfg)
        logger.debug('config is...')
        logger.debug(config)
    else:
        config = cfg
    # Allow default shell to be overriden by command-line argument
    shell_name = args['--shell']
    if shell_name:
        config['shell'] = SHELL_MAP.get(shell_name.lower(), AutoShell)
    start(**config)
    sys.exit(0)

if __name__ == '__main__':
    main()
