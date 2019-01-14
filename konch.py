#!/usr/bin/env python
"""konch: Customizes your Python shell.

Usage:
  konch
  konch init
  konch init [<config_file>] [-d]
  konch edit [-d]
  konch allow [<config_file>] [-d]
  konch deny [<config_file>] [-d]
  konch [--name=<name>] [-d]
  konch [--name=<name>] [--file=<file>] [--shell=<shell_name>] [-d]

Options:
  -h --help                  Show this screen.
  -v --version               Show version.
  init                       Creates a starter .konchrc file.
  edit                       Edit your .konchrc file.
  -n --name=<name>           Named config to use.
  -s --shell=<shell_name>    Shell to use. Can be either "ipy" (IPython),
                              "bpy" (BPython), "ptpy" (PtPython), "ptipy" (PtIPython),
                              "py" (built-in Python shell), or "auto".
                              Overrides the 'shell' option in .konchrc.
  -f --file=<file>           File path of konch config file to execute. If not provided,
                               konch will use the .konchrc file in the current
                               directory.
  -d --debug                 Enable debugging/verbose mode.

Environment variables:
  KONCH_AUTH_FILE: File where to store authorization data for config files.
    Defaults to ~/.local/share/konch_auth.
  KONCH_EDITOR: Editor command to use when running `konch edit`.
    Falls back to $VISUAL then $EDITOR.
"""

from __future__ import unicode_literals, print_function
from collections.abc import Iterable
import code
import codecs
import errno
import hashlib
import imp
import json
import logging
import os
import random
import subprocess
import sys
import warnings

from docopt import docopt

__version__ = "4.0.0.dev0"

logger = logging.getLogger(__name__)

BANNER_TEMPLATE = """{version}

{text}
{context}
"""


class KonchError(Exception):
    pass


class ShellNotAvailableError(KonchError):
    pass


class KonchrcNotAuthorizedError(KonchError):
    pass


class KonchrcChangedError(KonchrcNotAuthorizedError):
    pass


def _get_home_directory():
    return os.path.expanduser("~")


def _mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as error:
        if error.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


class AuthFile(object):
    def __init__(self, data):
        self.data = data

    def __repr__(self):
        return "AuthFile({!r})".format(self.data)

    @classmethod
    def load(cls):
        filepath = cls.get_path()
        try:
            with codecs.open(filepath, "r", "utf-8") as fp:
                data = json.load(fp)
        except FileNotFoundError:
            data = {}
        except json.JSONDecodeError as error:
            # File exists but is empty
            if error.doc.strip() == "":
                data = {}
            else:
                raise
        return cls(data)

    def allow(self, filepath):
        self.data[os.path.abspath(filepath)] = self._hash_file(filepath)

    def deny(self, filepath):
        if not os.path.exists(filepath):
            raise FileNotFoundError("{} not found".format(filepath))
        try:
            del self.data[os.path.abspath(filepath)]
        except KeyError:
            pass

    def check(self, filepath):
        if os.path.abspath(filepath) not in self.data:
            raise KonchrcNotAuthorizedError
        else:
            file_hash = self._hash_file(filepath)
            if file_hash != self.data[os.path.abspath(filepath)]:
                raise KonchrcChangedError
        return True

    def save(self):
        filepath = self.get_path()
        _mkdir_p(os.path.dirname(filepath))
        with codecs.open(filepath, "w", "utf-8") as fp:
            json.dump(self.data, fp)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        if not exc_type:
            self.save()

    @staticmethod
    def get_path():
        if "KONCH_AUTH_FILE" in os.environ:
            return os.environ["KONCH_AUTH_FILE"]
        elif "XDG_DATA_HOME" in os.environ:
            return os.path.join(os.environ["XDG_DATA_HOME"], "konch_auth")
        else:
            return os.path.join(_get_home_directory(), ".local", "share", "konch_auth")

    @staticmethod
    def _hash_file(filepath):
        # https://stackoverflow.com/a/22058673/1157536
        BUF_SIZE = 65536  # read in 64kb chunks
        sha1 = hashlib.sha1()
        with codecs.open(filepath, "rb") as f:
            while True:
                data = f.read(BUF_SIZE)
                if not data:
                    break
                sha1.update(data)
        return sha1.hexdigest()


CONFIG_FILE = ".konchrc"
DEFAULT_CONFIG_FILE = os.path.join(_get_home_directory(), ".konchrc.default")

INIT_TEMPLATE = """# vi: set ft=python :

import konch

# Available options:
#   "context", "banner", "shell", "prompt", "output",
#   "context_format", "ipy_extensions", "ipy_autoreload",
#   "ipy_colors", "ipy_highlighting_style"
konch.config({
    "context": {
        "speak": konch.speak,
    }
})


def setup():
    pass


def teardown():
    pass
"""


def _full_formatter(context):
    line_format = "{name}: {obj!r}"
    context_str = "\n".join(
        [
            line_format.format(name=name, obj=obj)
            for name, obj in sorted(context.items(), key=lambda i: i[0])
        ]
    )
    return "\nContext:\n{context}".format(context=context_str)


def _short_formatter(context):
    context_str = ", ".join(sorted(context.keys()))
    return "\nContext:\n{context}".format(context=context_str)


def _hide_formatter(context):
    return ""


CONTEXT_FORMATTERS = {
    "full": _full_formatter,
    "short": _short_formatter,
    "hide": _hide_formatter,
}


def format_context(context, formatter="full"):
    """Output the a context dictionary as a string."""
    if not context:
        return ""

    if callable(formatter):
        formatter_func = formatter
    else:
        if formatter in CONTEXT_FORMATTERS:
            formatter_func = CONTEXT_FORMATTERS[formatter]
        else:
            raise ValueError('Invalid context format: "{0}"'.format(formatter))
    return formatter_func(context)


def make_banner(text=None, context=None, banner_template=None, context_format="full"):
    """Generates a full banner with version info, the given text, and a
    formatted list of context variables.
    """
    banner_text = text or speak()
    banner_template = banner_template or BANNER_TEMPLATE
    context = format_context(context, formatter=context_format)
    out = banner_template.format(version=sys.version, text=banner_text, context=context)
    return out


def context_list2dict(context_list):
    """Converts a list of objects (functions, classes, or modules) to a
    dictionary mapping the object names to the objects.
    """
    return dict((obj.__name__, obj) for obj in context_list)


class Shell(object):
    """Base shell class.

    :param dict context: Dictionary, list, or callable (that returns a `dict` or `list`)
        that defines what variables will be available when the shell is run.
    :param str banner: Banner text that appears on startup.
    :param str prompt: Custom input prompt.
    :param str output: Custom output prompt.
    :param context_format: Formatter for the context dictionary in the banner.
        Either 'full', 'short', 'hide', or a function that receives the context
        dictionary and outputs a string.
    """

    banner_template = BANNER_TEMPLATE

    def __init__(
        self,
        context,
        banner=None,
        prompt=None,
        output=None,
        context_format="full",
        **kwargs
    ):
        self.context = context() if callable(context) else context
        self.context_format = context_format
        self.banner = make_banner(
            banner,
            self.context,
            context_format=self.context_format,
            banner_template=self.banner_template,
        )
        self.prompt = prompt
        self.output = output

    def check_availability(self):
        raise NotImplementedError

    def start(self):
        raise NotImplementedError


class PythonShell(Shell):
    """The built-in Python shell."""

    def check_availability(self):
        return True

    def start(self):
        try:
            import readline
        except ImportError:
            pass
        else:
            # We don't have to wrap the following import in a 'try', because
            # we already know 'readline' was imported successfully.
            import rlcompleter

            readline.set_completer(rlcompleter.Completer(self.context).complete)
            readline.parse_and_bind("tab:complete")

        if self.prompt:
            sys.ps1 = self.prompt
        if self.output:
            warnings.warn("Custom output templates not supported by PythonShell.")
        code.interact(self.banner, local=self.context)
        return None


def configure_ipython_prompt(config, prompt=None, output=None):
    import IPython

    if IPython.version_info[0] >= 5:  # Custom prompt API changed in IPython 5.0
        from pygments.token import Token

        # See https://ipython.readthedocs.io/en/stable/config/details.html#custom-prompts
        class CustomPrompt(IPython.terminal.prompts.Prompts):
            def in_prompt_tokens(self, *args, **kwargs):
                if prompt is None:
                    return super(CustomPrompt, self).in_prompt_tokens(*args, **kwargs)
                if isinstance(prompt, (str, bytes)):
                    return [(Token.Prompt, prompt)]
                else:
                    return prompt

            def out_prompt_tokens(self, *args, **kwargs):
                if output is None:
                    return super(CustomPrompt, self).out_prompt_tokens(*args, **kwargs)
                if isinstance(output, (str, bytes)):
                    return [(Token.OutPrompt, output)]
                else:
                    return prompt

        config.TerminalInteractiveShell.prompts_class = CustomPrompt
    else:
        prompt_config = config.PromptManager
        if prompt:
            prompt_config.in_template = prompt
        if output:
            prompt_config.out_template = output
    return None


class IPythonShell(Shell):
    """The IPython shell.

    :param list ipy_extensions: List of IPython extension names to load upon startup.
    :param bool ipy_autoreload: Whether to load and initialize the IPython autoreload
        extension upon startup. Can also be an integer, which will be passed as
        the argument to the %autoreload line magic.
    :param kwargs: The same kwargs as `Shell.__init__`.
    """

    def __init__(
        self,
        ipy_extensions=None,
        ipy_autoreload=False,
        ipy_colors=None,
        ipy_highlighting_style=None,
        *args,
        **kwargs
    ):
        self.ipy_extensions = ipy_extensions
        self.ipy_autoreload = ipy_autoreload
        self.ipy_colors = ipy_colors
        self.ipy_highlighting_style = ipy_highlighting_style
        Shell.__init__(self, *args, **kwargs)

    @staticmethod
    def init_autoreload(mode=2):
        """Load and initialize the IPython autoreload extension."""
        from IPython.extensions import autoreload

        ip = get_ipython()  # noqa: F821
        autoreload.load_ipython_extension(ip)
        ip.magics_manager.magics["line"]["autoreload"](str(mode))

    def check_availability(self):
        try:
            import IPython  # noqa: F401
        except ImportError:
            raise ShellNotAvailableError("IPython shell not available.")

    def start(self):
        try:
            from IPython import start_ipython
            from IPython.utils import io
            from traitlets.config.loader import Config as IPyConfig
        except ImportError:
            raise ShellNotAvailableError(
                "IPython shell not available " "or IPython version not supported."
            )
        # Hack to show custom banner
        # TerminalIPythonApp/start_app doesn't allow you to customize the banner directly,
        # so we write it to stdout before starting the IPython app
        io.stdout.write(self.banner)
        # Pass exec_lines in order to start autoreload
        if self.ipy_autoreload:
            if not isinstance(self.ipy_autoreload, bool):
                mode = self.ipy_autoreload
            else:
                mode = 2
            logger.debug(
                "Initializing IPython autoreload in mode {mode}".format(mode=mode)
            )
            exec_lines = [
                "import konch as __konch",
                "__konch.IPythonShell.init_autoreload({mode})".format(mode=mode),
            ]
        else:
            exec_lines = []
        ipy_config = IPyConfig()
        if self.ipy_colors:
            ipy_config.TerminalInteractiveShell.colors = self.ipy_colors
        if self.ipy_highlighting_style:
            ipy_config.TerminalInteractiveShell.highlighting_style = (
                self.ipy_highlighting_style
            )
        configure_ipython_prompt(ipy_config, prompt=self.prompt, output=self.output)
        # Use start_ipython rather than embed so that IPython is loaded in the "normal"
        # way. See https://github.com/django/django/pull/512
        start_ipython(
            display_banner=False,
            user_ns=self.context,
            config=ipy_config,
            extensions=self.ipy_extensions or [],
            exec_lines=exec_lines,
            argv=[],
        )
        return None


class PtPythonShell(Shell):
    def __init__(self, ptpy_vi_mode=False, *args, **kwargs):
        self.ptpy_vi_mode = ptpy_vi_mode
        Shell.__init__(self, *args, **kwargs)

    def check_availability(self):
        try:
            import ptpython  # noqa: F401
        except ImportError:
            raise ShellNotAvailableError("PtPython shell not available.")

    def start(self):
        try:
            from ptpython.repl import embed, run_config
        except ImportError:
            raise ShellNotAvailableError("PtPython shell not available.")
        print(self.banner)

        config_dir = os.path.expanduser("~/.ptpython/")

        # Startup path
        startup_paths = []
        if "PYTHONSTARTUP" in os.environ:
            startup_paths.append(os.environ["PYTHONSTARTUP"])

        # Apply config file
        def configure(repl):
            path = os.path.join(config_dir, "config.py")
            if os.path.exists(path):
                run_config(repl, path)

        embed(
            globals=self.context,
            history_filename=os.path.join(config_dir, "history"),
            vi_mode=self.ptpy_vi_mode,
            startup_paths=startup_paths,
            configure=configure,
        )
        return None


class PtIPythonShell(PtPythonShell):

    banner_template = "{text}\n{context}"

    def __init__(self, ipy_extensions=None, *args, **kwargs):
        self.ipy_extensions = ipy_extensions or []
        PtPythonShell.__init__(self, *args, **kwargs)

    def check_availability(self):
        try:
            import ptpython.ipython  # noqa: F401
            import IPython  # noqa: F401
        except ImportError:
            raise ShellNotAvailableError("PtIPython shell not available.")

    def start(self):
        try:
            from ptpython.ipython import embed
            from ptpython.repl import run_config
            from IPython.terminal.ipapp import load_default_config
            import six
        except ImportError:
            raise ShellNotAvailableError("PtIPython shell not available.")

        config_dir = os.path.expanduser("~/.ptpython/")

        # Apply config file
        def configure(repl):
            path = os.path.join(config_dir, "config.py")
            if os.path.exists(path):
                run_config(repl, path)

        # Startup path
        startup_paths = []
        if "PYTHONSTARTUP" in os.environ:
            startup_paths.append(os.environ["PYTHONSTARTUP"])
        # exec scripts from startup paths
        for path in startup_paths:
            if os.path.exists(path):
                with open(path, "rb") as f:
                    code = compile(f.read(), path, "exec")
                    six.exec_(code, self.context, self.context)
            else:
                print("File not found: {}\n\n".format(path))
                sys.exit(1)

        ipy_config = load_default_config()
        ipy_config.InteractiveShellEmbed = ipy_config.TerminalInteractiveShell
        ipy_config["InteractiveShellApp"]["extensions"] = self.ipy_extensions
        configure_ipython_prompt(ipy_config, prompt=self.prompt, output=self.output)
        embed(
            config=ipy_config,
            configure=configure,
            history_filename=os.path.join(config_dir, "history"),
            user_ns=self.context,
            header=self.banner,
            vi_mode=self.ptpy_vi_mode,
        )
        return None


class BPythonShell(Shell):
    """The BPython shell."""

    def check_availability(self):
        try:
            import bpython  # noqa: F401
        except ImportError:
            raise ShellNotAvailableError("BPython shell not available.")

    def start(self):
        try:
            from bpython import embed
        except ImportError:
            raise ShellNotAvailableError("BPython shell not available.")
        if self.prompt:
            warnings.warn("Custom prompts not supported by BPythonShell.")
        if self.output:
            warnings.warn("Custom output templates not supported by BPythonShell.")
        embed(banner=self.banner, locals_=self.context)
        return None


class AutoShell(Shell):
    """Shell that runs PtIpython, PtPython, IPython, or BPython if available.
    Falls back to built-in Python shell.
    """

    # Shell classes in precedence order
    SHELLS = [PtIPythonShell, PtPythonShell, IPythonShell, BPythonShell, PythonShell]

    def __init__(self, context, banner, **kwargs):
        Shell.__init__(self, context, **kwargs)
        self.kwargs = kwargs
        self.banner = banner

    def check_availability(self):
        return True

    def start(self):
        shell_args = {
            "context": self.context,
            "banner": self.banner,
            "prompt": self.prompt,
            "output": self.output,
            "context_format": self.context_format,
        }
        shell_args.update(self.kwargs)
        shell = None

        for shell_class in self.SHELLS:
            try:
                shell = shell_class(**shell_args)
                shell.check_availability()
            except ShellNotAvailableError:
                continue
            else:
                break
        return shell.start()


SHELL_MAP = {
    "ipy": IPythonShell,
    "ipython": IPythonShell,
    "bpy": BPythonShell,
    "bpython": BPythonShell,
    "py": PythonShell,
    "python": PythonShell,
    "auto": AutoShell,
    "ptpy": PtPythonShell,
    "ptpython": PtPythonShell,
    "ptipy": PtIPythonShell,
    "ptipython": PtIPythonShell,
}

CONCHES = [
    ('"My conch told me to come save you guys."\n' '"Hooray for the magic conches!"'),
    '"All hail the Magic Conch!"',
    '"Hooray for the magic conches!"',
    '"Uh, hello there. Magic Conch, I was wondering... '
    'should I have the spaghetti or the turkey?"',
    '"This copyrighted conch is the cornerstone of our organization."',
    '"Praise the Magic Conch!"',
    '"the conch exploded into a thousand white fragments and ceased to exist."',
    "\"S'right. It's a shell!\"",
    '"Ralph felt a kind of affectionate reverence for the conch"',
    '"Conch! Conch!"',
    '"That\'s why you got the conch out of the water"',
    '"the summons of the conch"',
    '"Whoever holds the conch gets to speak."',
    '"They\'ll come when they hear us--"',
    '"We gotta drop the load!"',
    '"Dude, we\'re falling right out the sky!!"',
    (
        '"Oh, Magic Conch Shell, what do we need to do to get out of the Kelp Forest?"\n'
        '"Nothing."'
    ),
    '"The shell knows all!"',
    '"we must never question the wisdom of the Magic Conch."',
    '"The Magic Conch! A club member!"',
    '"The shell has spoken!"',
    '"This copyrighted conch is the cornerstone of our organization."',
    '"All right, Magic Conch... what do we do now?"',
    '"Ohhh! The Magic Conch Shell! Ask it something! Ask it something!"',
]


def speak():
    return random.choice(CONCHES)


class Config(dict):
    """A dict-like config object. Behaves like a normal dict except that
    the ``context`` will always be converted from a list to a dict.
    Defines the default configuration.
    """

    def __init__(
        self,
        context=None,
        banner=None,
        shell=AutoShell,
        prompt=None,
        output=None,
        context_format="full",
        **kwargs
    ):
        ctx = Config.transform_val(context) or {}
        super(Config, self).__init__(
            context=ctx,
            banner=banner,
            shell=shell,
            prompt=prompt,
            output=output,
            context_format=context_format,
            **kwargs
        )

    def __setitem__(self, key, value):
        if key == "context":
            value = Config.transform_val(value)
        super(Config, self).__setitem__(key, value)

    @staticmethod
    def transform_val(val):
        if isinstance(val, (list, tuple)):
            return context_list2dict(val)
        return val

    def update(self, d):
        for key in d.keys():
            self[key] = d[key]


# _cfg and _config_registry are singletons that may be mutated in a .konchrc file
_cfg = Config()
_config_registry = {"default": _cfg}


def start(
    context=None,
    banner=None,
    shell=AutoShell,
    prompt=None,
    output=None,
    context_format="full",
    **kwargs
):
    """Start up the konch shell. Takes the same parameters as Shell.__init__.
    """
    logger.debug("Using shell: {!r}".format(shell))
    if banner is None:
        banner = speak()
    # Default to global config
    context_ = context or _cfg["context"]
    banner_ = banner or _cfg["banner"]
    if isinstance(shell, type) and issubclass(shell, Shell):
        shell_ = shell
    else:
        shell_ = SHELL_MAP.get(shell or _cfg["shell"], _cfg["shell"])
    prompt_ = prompt or _cfg["prompt"]
    output_ = output or _cfg["output"]
    context_format_ = context_format or _cfg["context_format"]
    shell_(
        context=context_,
        banner=banner_,
        prompt=prompt_,
        output=output_,
        context_format=context_format_,
        **kwargs
    ).start()


def config(config_dict):
    """Configures the konch shell. This function should be called in a
    .konchrc file.

    :param dict config_dict: Dict that may contain 'context', 'banner', and/or
        'shell' (default shell class to use).
    """
    logger.debug("Updating with {0}".format(config_dict))
    _cfg.update(config_dict)
    return _cfg


def named_config(name, config_dict):
    """Adds a named config to the config registry. The first argument may either be a string
    or a collection of strings.

    This function should be called in a .konchrc file.
    """
    names = (
        name
        if isinstance(name, Iterable) and not isinstance(name, (str, bytes))
        else [name]
    )
    for each in names:
        _config_registry[each] = Config(**config_dict)


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
        logger.debug("Adding {0} to sys.path".format(directory))
        sys.path.insert(0, directory)


def use_file(filename):
    """Load filename as a python file. Import ``filename`` and return it
    as a module.
    """
    config_file = filename or resolve_path(CONFIG_FILE)

    def preview_unauthorized():
        print()
        print("*" * 46, file=sys.stderr)
        print(file=sys.stderr)
        with codecs.open(config_file, "r", "utf-8") as fp:
            for line in fp:
                print(line, end="", file=sys.stderr)
        print(file=sys.stderr)
        print("*" * 46, file=sys.stderr)
        print(file=sys.stderr)
        print(
            "Verify the file's contents and run `konch allow` to approve it.",
            file=sys.stderr,
        )

    if config_file and not os.path.exists(config_file):
        print('"{}" not found.'.format(filename), file=sys.stderr)
        sys.exit(1)
    if config_file and os.path.exists(config_file):
        with AuthFile.load() as authfile:
            try:
                authfile.check(config_file)
            except KonchrcChangedError:
                print(
                    '"{}" has changed since you last used it.'.format(config_file),
                    file=sys.stderr,
                )
                preview_unauthorized()
                sys.exit(1)
            except KonchrcNotAuthorizedError:
                print('"{}" is blocked.'.format(config_file), file=sys.stderr)
                preview_unauthorized()
                sys.exit(1)

        logger.info("Using {0}".format(config_file))
        # Ensure that relative imports are possible
        __ensure_directory_in_path(config_file)
        mod = None
        try:
            mod = imp.load_source("konchrc", config_file)
        except UnboundLocalError:  # File not found
            pass
        else:
            try:
                # Clean up bytecode file on PY2
                os.remove(config_file + "c")
            except (IOError, OSError):
                pass
            return mod
    if not config_file:
        warnings.warn("No config file found.")
    else:
        warnings.warn('"{fname}" not found.'.format(fname=config_file))


def resolve_path(filename):
    """Find a file by walking up parent directories until the file is found.
    Return the absolute path of the file.
    """
    current = os.getcwd()
    # Stop search at home directory
    sentinel_dir = os.path.abspath(os.path.join(_get_home_directory(), ".."))
    while current != sentinel_dir:
        target = os.path.join(current, filename)
        if os.path.exists(target):
            return os.path.abspath(target)
        else:
            current = os.path.abspath(os.path.join(current, ".."))

    return False


def get_editor():
    for key in "KONCH_EDITOR", "VISUAL", "EDITOR":
        ret = os.environ.get(key)
        if ret:
            return ret
    if sys.platform.startswith("win"):
        return "notepad"
    for editor in "vim", "nano":
        if os.system("which %s &> /dev/null" % editor) == 0:
            return editor
    return "vi"


def edit_file(filename, editor=None):
    editor = editor or get_editor()
    try:
        result = subprocess.Popen('{0} "{1}"'.format(editor, filename), shell=True)
        exit_code = result.wait()
        if exit_code != 0:
            print("{0}: Editing failed!".format(editor), file=sys.stderr)
            sys.exit(1)
    except OSError as err:
        print("{0}: Editing failed: {1}".format(editor, err), file=sys.stderr)
        sys.exit(1)
    else:
        with AuthFile.load() as authfile:
            authfile.allow(filename)


def init_config(config_file):
    if not os.path.exists(config_file):
        init_template = INIT_TEMPLATE
        if os.path.exists(DEFAULT_CONFIG_FILE):  # use ~/.konchrc.default if it exists
            with open(DEFAULT_CONFIG_FILE, "r") as fp:
                init_template = fp.read()
        with open(config_file, "w") as fp:
            fp.write(init_template)
        with AuthFile.load() as authfile:
            authfile.allow(config_file)
        print(
            "Initialized konch. Edit {0} to your needs and run `konch` "
            "to start an interactive session.".format(config_file)
        )
        sys.exit(0)
    else:
        print(
            "{0} already exists in this directory.".format(config_file), file=sys.stderr
        )
        sys.exit(1)


def edit_config(config_file=None, editor=None):
    filename = config_file or resolve_path(CONFIG_FILE)
    print('Editing file: "{0}"'.format(filename))
    edit_file(filename, editor=editor)
    sys.exit(0)


def allow_config(config_file=None):
    if config_file and os.path.isdir(config_file):
        filename = os.path.join(config_file, CONFIG_FILE)
    else:
        filename = config_file or resolve_path(CONFIG_FILE)
    if not filename:
        print("No config file found.", file=sys.stderr)
        sys.exit(1)
    print('Authorizing "{}"...'.format(filename))
    with AuthFile.load() as authfile:
        try:
            authfile.allow(filename)
        except FileNotFoundError:
            print('"{}" does not exist.'.format(filename), file=sys.stderr)
            sys.exit(1)
        else:
            print("Done. You can now start a shell with `konch`.")
    sys.exit(0)


def deny_config(config_file=None):
    if config_file and os.path.isdir(config_file):
        filename = os.path.join(config_file, CONFIG_FILE)
    else:
        filename = config_file or resolve_path(CONFIG_FILE)
    if not filename:
        print("No config file found.", file=sys.stderr)
        sys.exit(1)
    print('Removing authorization for "{}"...'.format(filename))
    with AuthFile.load() as authfile:
        try:
            authfile.deny(filename)
        except FileNotFoundError:
            print("{} does not exist.".format(filename), file=sys.stderr)
            sys.exit(1)
        else:
            print("Done.")
    sys.exit(0)


def parse_args():
    """Exposes the docopt command-line arguments parser.
    Return a dictionary of arguments.
    """
    return docopt(__doc__, version=__version__)


def main():
    """Main entry point for the konch CLI."""
    args = parse_args()

    if args["--debug"]:
        logging.basicConfig(
            format="%(levelname)s %(filename)s: %(message)s", level=logging.DEBUG
        )
    logger.debug(args)

    if args["init"]:
        config_file = args["<config_file>"] or CONFIG_FILE
        init_config(config_file)
    elif args["edit"]:
        edit_config(args["<config_file>"])
    elif args["allow"]:
        allow_config(args["<config_file>"])
    elif args["deny"]:
        deny_config(args["<config_file>"])

    mod = use_file(args["--file"])
    if hasattr(mod, "setup"):
        mod.setup()

    if args["--name"]:
        if args["--name"] not in _config_registry:
            print('Invalid --name: "{}"'.format(args["--name"]), file=sys.stderr)
            sys.exit(1)
        config_dict = _config_registry[args["--name"]]
        logger.debug('Using named config: "{}"...'.format(args["--name"]))
        logger.debug(config_dict)
    else:
        config_dict = _cfg
    # Allow default shell to be overriden by command-line argument
    shell_name = args["--shell"]
    if shell_name:
        config_dict["shell"] = SHELL_MAP.get(shell_name.lower(), AutoShell)
    logger.debug("Starting with config {0}".format(config_dict))
    start(**config_dict)

    if hasattr(mod, "teardown"):
        mod.teardown()
    sys.exit(0)


if __name__ == "__main__":
    main()
