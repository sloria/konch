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
  -n --name=<name>           Named config to use.
  -s --shell=<shell_name>    Shell to use. Can be either "ipy" (IPython),
                              "bpy" (BPython), "py" (built-in Python shell),
                               or "auto". Overrides the 'shell' option in .konchrc.
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

__version__ = '0.3.3-dev'
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


DEFAULT_CONFIG_FILE = '.konchrc'

INIT_TEMPLATE = '''# -*- coding: utf-8 -*-
import konch

# TODO: Edit me
# Available options: 'context', 'banner', 'shell', 'prompt'
konch.config({
    'context': {
        'speak': konch.speak
    }
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


def make_banner(text=None, context=None, hide_context=False):
    """Generates a full banner with version info, the given text, and a
    formatted list of context variables.
    """
    banner_text = text or speak()
    out = BANNER_TEMPLATE.format(version=sys.version, text=banner_text)
    if context and not hide_context:
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
    :param str prompt: Custom input prompt.
    :param str output: Custom output prompt.
    """

    def __init__(self, context, banner=None, prompt=None,
            output=None, hide_context=False):
        self.context = context
        self.hide_context = hide_context
        self.banner = make_banner(banner, context, hide_context=hide_context)
        self.prompt = prompt
        self.output = output

    def start(self):
        raise NotImplementedError


class PythonShell(Shell):
    """The built-in Python shell."""

    def start(self):
        if self.prompt:
            sys.ps1 = self.prompt
        if self.output:
            warnings.warn('Custom output templates not supported by PythonShell.')
        code.interact(self.banner, local=self.context)
        return None


class IPythonShell(Shell):
    """The IPython shell."""

    def start(self):
        try:
            from IPython import embed
            from IPython.config.loader import Config as IPyConfig
        except ImportError:
            raise ShellNotAvailableError('IPython shell not available.')
        ipy_config = IPyConfig()
        prompt_config = ipy_config.PromptManager
        if self.prompt:
            prompt_config.in_template = self.prompt
        if self.output:
            prompt_config.out_template = self.output
        embed(banner1=self.banner,
            user_ns=self.context,
            config=ipy_config)
        return None


class BPythonShell(Shell):
    """The BPython shell."""

    def start(self):
        try:
            from bpython import embed
        except ImportError:
            raise ShellNotAvailableError('BPython shell not available.')
        if self.prompt:
            warnings.warn('Custom prompts not supported by BPythonShell.')
        if self.output:
            warnings.warn('Custom output templates not supported by BPythonShell.')
        embed(banner=self.banner, locals_=self.context)
        return None


class AutoShell(Shell):
    """Shell that runs IPython or BPython if available. Falls back to built-in
    Python shell.
    """

    def __init__(self, context, banner, *args, **kwargs):
        Shell.__init__(self, context, *args, **kwargs)
        self.banner = banner

    def start(self):
        shell_args = {
            'context': self.context,
            'banner': self.banner,
            'prompt': self.prompt,
            'output': self.output,
            'hide_context': self.hide_context,
        }
        try:
            return IPythonShell(**shell_args).start()
        except ShellNotAvailableError:
            try:
                return BPythonShell(**shell_args).start()
            except ShellNotAvailableError:
                return PythonShell(**shell_args).start()
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
    '"That\'s why you got the conch out of the water"',
    '"the summons of the conch"',
    '"Whoever holds the conch gets to speak."',
    '"They\'ll come when they hear us--"',
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
    Defines the default configuration.
    """

    def __init__(self, context=None, banner=None, shell=AutoShell,
            prompt=None, output=None, hide_context=False):
        ctx = Config.transform_val(context) or {}
        super(Config, self).__init__(context=ctx, banner=banner, shell=shell,
            prompt=prompt, output=output, hide_context=hide_context)

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

# _cfg and _config_registry are global variables that may be mutated by a
# .konchrc file
_cfg = Config()
_config_registry = {
    'default': _cfg
}


def start(context=None, banner=None, shell=AutoShell,
        prompt=None, output=None, hide_context=False):
    """Start up the konch shell. Takes the same parameters as Shell.__init__.
    """
    logger.debug('Using shell...')
    logger.debug(shell)
    if banner is None:
        banner = speak()
    # Default to global config
    context_ = context or _cfg['context']
    banner_ = banner or _cfg['banner']
    shell_ = shell or _cfg['shell']
    prompt_ = prompt or _cfg['prompt']
    output_ = output or _cfg['output']
    hide_context_ = hide_context or _cfg['hide_context']
    shell_(context=context_, banner=banner_,
        prompt=prompt_, output=output_, hide_context=hide_context_).start()


def config(config_dict):
    """Configures the konch shell. This function should be called in a
    .konchrc file.

    :param dict config_dict: Dict that may contain 'context', 'banner', and/or
        'shell' (default shell class to use).
    """
    logger.debug('Updating with {0}'.format(config_dict))
    _cfg.update(config_dict)
    return _cfg


def named_config(name, config_dict):
    """Adds a named config to the config registry.
    This function should be called in a .konchrc file.
    """
    _config_registry[name] = Config(**config_dict)


def reset_config():
    global _cfg
    _cfg = Config()
    return _cfg


def get_file_directory(filename):
    return os.path.dirname(os.path.abspath(filename))


def __ensure_directory_in_path(filename):
    """Ensures that a file's directory is in the Python path.
    """
    directory = get_file_directory(filename)
    if directory not in sys.path:
        logger.debug('Adding {0} to sys.path'.format(directory))
        sys.path.insert(0, directory)


def use_file(filename):
    # First update _cfg by executing the config file
    config_file = filename or resolve_path(DEFAULT_CONFIG_FILE)
    if config_file and os.path.exists(config_file):
        logger.info('Using {0}'.format(config_file))
        # Ensure that relative imports are possible
        __ensure_directory_in_path(config_file)
        execute_file(config_file)
    else:
        if not config_file:
            warnings.warn('No config file found.')
        else:
            warnings.warn('"{fname}" not found.'.format(fname=config_file))
    return _cfg


def __get_home_directory():
    return os.path.expanduser('~')


def resolve_path(filename):
    """Find a file by walking up parent directories until the file is found.
    Return the absolute path of the file.
    """
    current = os.getcwd()
    sentinal_dir = os.path.join(__get_home_directory(), '..')
    while current != sentinal_dir:
        target = os.path.join(current, filename)
        if os.path.exists(target):
            return os.path.abspath(target)
        else:
            current = os.path.abspath(os.path.join(current, '..'))

    return False


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


def parse_args():
    """Exposes the docopt command-line arguments parser.
    Return a dictionary of arguments.
    """
    return docopt(__doc__, version=__version__)


def main():
    """Main entry point for the konch CLI."""
    args = parse_args()
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
        config_dict = _config_registry.get(args['--name'], _cfg)
        logger.debug('Using named config...')
        logger.debug(config)
    else:
        config_dict = _cfg
    # Allow default shell to be overriden by command-line argument
    shell_name = args['--shell']
    if shell_name:
        config_dict['shell'] = SHELL_MAP.get(shell_name.lower(), AutoShell)
    logger.debug('Starting with config {0}'.format(config_dict))
    start(**config_dict)
    sys.exit(0)

if __name__ == '__main__':
    main()
