#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''konch: Custom Python Shell

Usage:
  konch
  konch init
  konch init [<config_file>] [-d]
  konch [--file=<file>] [--shell=<shell_name>] [-d]

Options:
  -h --help                  Show this screen.
  -v --version               Show version.
  init                       Creates a starter .konchrc file.
  -s --shell=<shell_name>    Shell to use. Can be either "ipy" (IPython),
                              "bpy" (BPython), or "py" (built-in Python shell),
                               or "auto" (try to use IPython or Bpython and
                               fallback to built-in shell).
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
import copy
import warnings

from docopt import docopt

__version__ = '0.1.0'
__author__ = 'Steven Loria'
__license__ = 'MIT'

logger = logging.getLogger(__name__)


def execute_file(fname, globals_=None, locals_=None):
    exec(compile(open(fname, "rb").read(), fname, 'exec'), globals_, locals_)

BANNER_TEMPLATE = """{version}

{text}
"""

CONTEXT_TEMPLATE = """
Context:
{context}
"""

DEFAULT_BANNER_TEXT = 'Welcome to the konch shell. Happy hacking!'

DEFAULT_CONFIG_FILE = '.konchrc'

INIT_TEMPLATE = """#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import random

import konch

# TODO: Edit me
context = {
    'os': os,
    'random': random,
}

# Available options: "context", "banner", "shell"
konch.config({
    'context': context,
})
"""


def format_context(context):
    if context is None:
        return ''
    line_format = '{name}: {obj!r}'
    return '\n'.join([
        line_format.format(name=name, obj=obj)
        for name, obj in context.items()
    ])


def make_banner(text=None, context=None):
    banner_text = text or DEFAULT_BANNER_TEXT
    out = BANNER_TEMPLATE.format(version=sys.version, text=banner_text)
    if context:
        out += CONTEXT_TEMPLATE.format(context=format_context(context))
    return out


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


class ArbokError(Exception):
    pass


class ShellNotAvailableError(ArbokError):
    pass

SHELL_MAP = {
    'ipy': IPythonShell, 'ipython': IPythonShell,
    'bpy': BPythonShell, 'bpython': BPythonShell,
    'py': PythonShell, 'python': PythonShell,
    'auto': AutoShell,
}


DEFAULT_OPTIONS = {
    'shell': AutoShell,
    'banner': DEFAULT_BANNER_TEXT,
    'context': {}
}

#: Global configuration object. Defines default options for start().
cfg = copy.deepcopy(DEFAULT_OPTIONS)


def start(context, banner=None, shell=AutoShell):
    """Start up the konch shell with a given context."""
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


def reset_config():
    global cfg
    cfg = copy.deepcopy(DEFAULT_OPTIONS)
    return cfg


def __update_cfg_from_args(args):
    # First update cfg by executing the config file
    config_file = args['--file'] or DEFAULT_CONFIG_FILE
    if os.path.exists(config_file):
        logger.info('Using {0}'.format(config_file))
        execute_file(config_file)
    else:
        warnings.warn('"{0}" not found.'.format(config_file))
    # Allow default shell to be overriden by command-line argument
    shell_name = args['--shell']
    if shell_name:
        cfg['shell'] = SHELL_MAP.get(shell_name.lower(), AutoShell)
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
    __update_cfg_from_args(args)
    start(**cfg)
    sys.exit(0)

if __name__ == '__main__':
    main()
