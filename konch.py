#!/usr/bin/env python3
"""konch: Customizes your Python shell.

Usage:
  konch
  konch init [<config_file>] [-d]
  konch edit [<config_file>] [-d]
  konch allow [<config_file>] [-d]
  konch deny [<config_file>] [-d]
  konch [--name=<name>] [--file=<file>] [--shell=<shell_name>] [-d]

Options:
  -h --help                  Show this screen.
  -v --version               Show version.
  init                       Creates a starter .konchrc file.
  edit                       Edit your .konchrc file.
  -n --name=<name>           Named config to use.
  -s --shell=<shell_name>    Shell to use. Can be either "ipy" (IPython),
                              "bpy" (BPython), "bpyc" (BPython Curses),
                              "ptpy" (PtPython), "ptipy" (PtIPython),
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
  NO_COLOR: Disable ANSI colors.
"""
from collections.abc import Iterable
from importlib.machinery import SourceFileLoader
from pathlib import Path
import code
import hashlib
import json
import logging
import os
import random
import subprocess
import sys
import typing
import types
import warnings

from docopt import docopt

__version__ = "4.3.0"

logger = logging.getLogger(__name__)


class KonchError(Exception):
    pass


class ShellNotAvailableError(KonchError):
    pass


class NoNameError(KonchError):
    def __init__(self, message: str, obj: typing.Any):
        self.obj = obj
        super().__init__(message)


class KonchrcNotAuthorizedError(KonchError):
    pass


class KonchrcChangedError(KonchrcNotAuthorizedError):
    pass


class AuthFile:
    def __init__(self, data: typing.Dict[str, str]) -> None:
        self.data = data

    def __repr__(self) -> str:
        return f"AuthFile({self.data!r})"

    @classmethod
    def load(cls, path: typing.Optional[Path] = None) -> "AuthFile":
        filepath = path or cls.get_path()
        try:
            with Path(filepath).open("r", encoding="utf-8") as fp:
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

    def allow(self, filepath: Path) -> None:
        logger.debug(f"Authorizing {filepath}")
        self.data[str(Path(filepath).resolve())] = self._hash_file(filepath)

    def deny(self, filepath: Path) -> None:
        if not filepath.exists():
            raise FileNotFoundError(f"{filepath} not found")
        try:
            logger.debug(f"Removing authorization for {filepath}")
            del self.data[str(filepath.resolve())]
        except KeyError:
            pass

    def check(
        self, filepath: typing.Union[Path, None], raise_error: bool = True
    ) -> bool:
        if not filepath:
            return False
        if str(filepath.resolve()) not in self.data:
            if raise_error:
                raise KonchrcNotAuthorizedError
            else:
                return False
        else:
            file_hash = self._hash_file(filepath)
            if file_hash != self.data[str(filepath.resolve())]:
                if raise_error:
                    raise KonchrcChangedError
                else:
                    return False
        return True

    def save(self) -> None:
        filepath = self.get_path()
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with Path(filepath).open("w", encoding="utf-8") as fp:
            json.dump(self.data, fp)

    def __enter__(self) -> "AuthFile":
        return self

    def __exit__(
        self,
        exc_type: typing.Type[Exception],
        exc_value: Exception,
        exc_traceback: types.TracebackType,
    ) -> None:
        if not exc_type:
            self.save()

    @staticmethod
    def get_path() -> Path:
        if "KONCH_AUTH_FILE" in os.environ:
            return Path(os.environ["KONCH_AUTH_FILE"])
        elif "XDG_DATA_HOME" in os.environ:
            return Path(os.environ["XDG_DATA_HOME"]) / "konch_auth"
        else:
            return Path.home() / ".local" / "share" / "konch_auth"

    @staticmethod
    def _hash_file(filepath: Path) -> str:
        # https://stackoverflow.com/a/22058673/1157536
        BUF_SIZE = 65536  # read in 64kb chunks
        sha1 = hashlib.sha1()
        with Path(filepath).open("rb") as f:
            while True:
                data = f.read(BUF_SIZE)
                if not data:
                    break
                sha1.update(data)  # type: ignore
        return sha1.hexdigest()


RED = 31
GREEN = 32
YELLOW = 33
BOLD = 1
RESET_ALL = 0


def style(
    text: str,
    fg: typing.Optional[int] = None,
    *,
    bold: bool = False,
    file: typing.IO = sys.stdout,
) -> str:
    use_color = not os.environ.get("NO_COLOR") and file.isatty()
    if use_color:
        parts = [
            fg and f"\033[{fg}m",
            bold and f"\033[{BOLD}m",
            text,
            f"\033[{RESET_ALL}m",
        ]
        return "".join([e for e in parts if e])
    else:
        return text


def sprint(text: str, *args: typing.Any, **kwargs: typing.Any) -> None:
    file = kwargs.pop("file", sys.stdout)
    return print(style(text, file=file, *args, **kwargs), file=file)


def print_error(text: str) -> None:
    prefix = style("ERROR", RED, file=sys.stderr)
    return sprint(f"{prefix}: {text}", file=sys.stderr)


def print_warning(text: str) -> None:
    prefix = style("WARNING", YELLOW, file=sys.stderr)
    return sprint(f"{prefix}: {text}", file=sys.stderr)


Context = typing.Mapping[str, typing.Any]
Formatter = typing.Callable[[Context], str]
ContextFormat = typing.Union[str, Formatter]


def _full_formatter(context: Context) -> str:
    line_format = "{name}: {obj!r}"
    context_str = "\n".join(
        [
            line_format.format(name=name, obj=obj)
            for name, obj in sorted(context.items(), key=lambda i: i[0].lower())
        ]
    )
    header = style("Context:", bold=True)
    return f"\n{header}\n{context_str}"


def _short_formatter(context: Context) -> str:
    context_str = ", ".join(sorted(context.keys(), key=str.lower))
    header = style("Context:", bold=True)
    return f"\n{header}\n{context_str}"


def _hide_formatter(context: Context) -> str:
    return ""


CONTEXT_FORMATTERS: typing.Dict[str, Formatter] = {
    "full": _full_formatter,
    "short": _short_formatter,
    "hide": _hide_formatter,
}


def format_context(
    context: Context, formatter: typing.Union[str, Formatter] = "full"
) -> str:
    """Output the a context dictionary as a string."""
    if not context:
        return ""

    if callable(formatter):
        formatter_func = formatter
    else:
        if formatter in CONTEXT_FORMATTERS:
            formatter_func = CONTEXT_FORMATTERS[formatter]
        else:
            raise ValueError(f'Invalid context format: "{formatter}"')
    return formatter_func(context)


BANNER_TEMPLATE = """{version}

{text}
{context}
"""


def make_banner(
    text: typing.Optional[str] = None,
    context: typing.Optional[Context] = None,
    banner_template: typing.Optional[str] = None,
    context_format: ContextFormat = "full",
) -> str:
    """Generates a full banner with version info, the given text, and a
    formatted list of context variables.
    """
    banner_text = text or speak()
    banner_template = banner_template or BANNER_TEMPLATE
    ctx = format_context(context or {}, formatter=context_format)
    out = banner_template.format(version=sys.version, text=banner_text, context=ctx)
    return out


def get_name(obj: typing.Any) -> str:
    try:
        fullname = obj.__name__
    except AttributeError as error:
        raise NoNameError(f"Object {obj} has no __name__", obj) from error
    return fullname.split(".")[-1]


def context_list2dict(context_list: typing.Sequence[typing.Any]) -> Context:
    """Converts a list of objects (functions, classes, or modules) to a
    dictionary mapping the object names to the objects.
    """
    return {get_name(obj): obj for obj in context_list}


def _relpath(p: Path) -> Path:
    return p.resolve().relative_to(Path.cwd())


class Shell:
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

    banner_template: str = BANNER_TEMPLATE

    def __init__(
        self,
        context: Context,
        banner: typing.Optional[str] = None,
        prompt: typing.Optional[str] = None,
        output: typing.Optional[str] = None,
        context_format: ContextFormat = "full",
        **kwargs: typing.Any,
    ) -> None:
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

    def check_availability(self) -> bool:
        raise NotImplementedError

    def start(self) -> None:
        raise NotImplementedError


class PythonShell(Shell):
    """The built-in Python shell."""

    def check_availability(self) -> bool:
        return True

    def start(self) -> None:
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


def configure_ipython_prompt(
    config, prompt: typing.Optional[str] = None, output: typing.Optional[str] = None
) -> None:
    import IPython

    if IPython.version_info[0] >= 5:  # Custom prompt API changed in IPython 5.0
        from pygments.token import Token

        # https://ipython.readthedocs.io/en/stable/config/details.html#custom-prompts  # noqa: B950
        class CustomPrompt(IPython.terminal.prompts.Prompts):
            def in_prompt_tokens(self, *args, **kwargs):
                if prompt is None:
                    return super().in_prompt_tokens(*args, **kwargs)
                if isinstance(prompt, (str, bytes)):
                    return [(Token.Prompt, prompt)]
                else:
                    return prompt

            def out_prompt_tokens(self, *args, **kwargs):
                if output is None:
                    return super().out_prompt_tokens(*args, **kwargs)
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
        ipy_extensions: typing.Optional[typing.List[str]] = None,
        ipy_autoreload: bool = False,
        ipy_colors: typing.Optional[str] = None,
        ipy_highlighting_style: typing.Optional[str] = None,
        *args: typing.Any,
        **kwargs: typing.Any,
    ):
        self.ipy_extensions = ipy_extensions
        self.ipy_autoreload = ipy_autoreload
        self.ipy_colors = ipy_colors
        self.ipy_highlighting_style = ipy_highlighting_style
        Shell.__init__(self, *args, **kwargs)

    @staticmethod
    def init_autoreload(mode: int) -> None:
        """Load and initialize the IPython autoreload extension."""
        from IPython.extensions import autoreload

        ip = get_ipython()  # type: ignore # noqa: F821
        autoreload.load_ipython_extension(ip)
        ip.magics_manager.magics["line"]["autoreload"](str(mode))

    def check_availability(self) -> bool:
        try:
            import IPython  # noqa: F401
        except ImportError:
            raise ShellNotAvailableError("IPython shell not available.")
        return True

    def start(self) -> None:
        try:
            from IPython import start_ipython
            from IPython.utils import io
            from traitlets.config.loader import Config as IPyConfig
        except ImportError:
            raise ShellNotAvailableError(
                "IPython shell not available " "or IPython version not supported."
            )
        # Hack to show custom banner
        # TerminalIPythonApp/start_app doesn't allow you to customize the
        # banner directly, so we write it to stdout before starting the IPython app
        io.stdout.write(self.banner)
        # Pass exec_lines in order to start autoreload
        if self.ipy_autoreload:
            if not isinstance(self.ipy_autoreload, bool):
                mode = self.ipy_autoreload
            else:
                mode = 2
            logger.debug(f"Initializing IPython autoreload in mode {mode}")
            exec_lines = [
                "import konch as __konch",
                f"__konch.IPythonShell.init_autoreload({mode})",
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
    def __init__(self, ptpy_vi_mode: bool = False, *args, **kwargs):
        self.ptpy_vi_mode = ptpy_vi_mode
        Shell.__init__(self, *args, **kwargs)

    def check_availability(self) -> bool:
        try:
            import ptpython  # noqa: F401
        except ImportError:
            raise ShellNotAvailableError("PtPython shell not available.")
        return True

    def start(self) -> None:
        try:
            from ptpython.repl import embed, run_config
        except ImportError:
            raise ShellNotAvailableError("PtPython shell not available.")
        print(self.banner)

        config_dir = Path("~/.ptpython/").expanduser()

        # Startup path
        startup_paths = []
        if "PYTHONSTARTUP" in os.environ:
            startup_paths.append(os.environ["PYTHONSTARTUP"])

        # Apply config file
        def configure(repl):
            path = config_dir / "config.py"
            if path.exists():
                run_config(repl, str(path))

        embed(
            globals=self.context,
            history_filename=config_dir / "history",
            vi_mode=self.ptpy_vi_mode,
            startup_paths=startup_paths,
            configure=configure,
        )
        return None


class PtIPythonShell(PtPythonShell):

    banner_template: str = "{text}\n{context}"

    def __init__(
        self, ipy_extensions: typing.Optional[typing.List[str]] = None, *args, **kwargs
    ) -> None:
        self.ipy_extensions = ipy_extensions or []
        PtPythonShell.__init__(self, *args, **kwargs)

    def check_availability(self) -> bool:
        try:
            import ptpython.ipython  # noqa: F401
            import IPython  # noqa: F401
        except ImportError:
            raise ShellNotAvailableError("PtIPython shell not available.")
        return True

    def start(self) -> None:
        try:
            from ptpython.ipython import embed
            from ptpython.repl import run_config
            from IPython.terminal.ipapp import load_default_config
        except ImportError:
            raise ShellNotAvailableError("PtIPython shell not available.")

        config_dir = Path("~/.ptpython/").expanduser()

        # Apply config file
        def configure(repl):
            path = config_dir / "config.py"
            if path.exists():
                run_config(repl, str(path))

        # Startup path
        startup_paths = []
        if "PYTHONSTARTUP" in os.environ:
            startup_paths.append(os.environ["PYTHONSTARTUP"])
        # exec scripts from startup paths
        for path in startup_paths:
            if Path(path).exists():
                with Path(path).open("rb") as f:
                    code = compile(f.read(), path, "exec")
                    exec(code, self.context, self.context)
            else:
                print(f"File not found: {path}\n\n")
                sys.exit(1)

        ipy_config = load_default_config()
        ipy_config.InteractiveShellEmbed = ipy_config.TerminalInteractiveShell
        ipy_config["InteractiveShellApp"]["extensions"] = self.ipy_extensions
        configure_ipython_prompt(ipy_config, prompt=self.prompt, output=self.output)
        embed(
            config=ipy_config,
            configure=configure,
            history_filename=config_dir / "history",
            user_ns=self.context,
            header=self.banner,
            vi_mode=self.ptpy_vi_mode,
        )
        return None


class BPythonShell(Shell):
    """The BPython shell."""

    def check_availability(self) -> bool:
        try:
            import bpython  # noqa: F401
        except ImportError:
            raise ShellNotAvailableError("BPython shell not available.")
        return True

    def start(self) -> None:
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


class BPythonCursesShell(Shell):
    """The BPython Curses shell."""

    def check_availability(self) -> bool:
        try:
            import bpython.cli  # noqa: F401
        except ImportError:
            raise ShellNotAvailableError("BPython Curses shell not available.")
        return True

    def start(self) -> None:
        try:
            from bpython.cli import main
        except ImportError:
            raise ShellNotAvailableError("BPython Curses shell not available.")
        if self.prompt:
            warnings.warn("Custom prompts not supported by BPython Curses shell.")
        if self.output:
            warnings.warn(
                "Custom output templates not supported by BPython Curses shell."
            )
        main(banner=self.banner, locals_=self.context, args=["-i", "-q"])
        return None


class AutoShell(Shell):
    """Shell that runs PtIpython, PtPython, IPython, or BPython if available.
    Falls back to built-in Python shell.
    """

    # Shell classes in precedence order
    SHELLS = [
        PtIPythonShell,
        PtPythonShell,
        IPythonShell,
        BPythonShell,
        BPythonCursesShell,
        PythonShell,
    ]

    def __init__(self, context: Context, banner: str, **kwargs):
        Shell.__init__(self, context, **kwargs)
        self.kwargs = kwargs
        self.banner = banner

    def check_availability(self) -> bool:
        return True

    def start(self) -> None:
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
        else:
            raise ShellNotAvailableError("No available shell to run.")
        return shell.start()


CONCHES: typing.List[str] = [
    '"My conch told me to come save you guys."\n"Hooray for the magic conches!"',
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
        '"Oh, Magic Conch Shell, what do we need to do to get '
        'out of the Kelp Forest?"\n"Nothing."'
    ),
    '"The shell knows all!"',
    '"we must never question the wisdom of the Magic Conch."',
    '"The Magic Conch! A club member!"',
    '"The shell has spoken!"',
    '"This copyrighted conch is the cornerstone of our organization."',
    '"All right, Magic Conch... what do we do now?"',
    '"Ohhh! The Magic Conch Shell! Ask it something! Ask it something!"',
]


def speak() -> str:
    return random.choice(CONCHES)


class Config(dict):
    """A dict-like config object. Behaves like a normal dict except that
    the ``context`` will always be converted from a list to a dict.
    Defines the default configuration.
    """

    def __init__(
        self,
        context: typing.Optional[Context] = None,
        banner: typing.Optional[str] = None,
        shell: typing.Type[Shell] = AutoShell,
        prompt: typing.Optional[str] = None,
        output: typing.Optional[str] = None,
        context_format: str = "full",
        **kwargs: typing.Any,
    ) -> None:
        ctx = Config.transform_val(context) or {}
        super().__init__(
            context=ctx,
            banner=banner,
            shell=shell,
            prompt=prompt,
            output=output,
            context_format=context_format,
            **kwargs,
        )

    def __setitem__(self, key: typing.Any, value: typing.Any) -> None:
        if key == "context":
            value = Config.transform_val(value)
        super().__setitem__(key, value)

    @staticmethod
    def transform_val(val: typing.Any) -> typing.Any:
        if isinstance(val, (list, tuple)):
            return context_list2dict(val)
        return val

    def update(self, d: typing.Mapping) -> None:  # type: ignore
        for key in d.keys():
            # Shallow-merge context
            if key == "context":
                self["context"].update(Config.transform_val(d["context"]))
            else:
                self[key] = d[key]


SHELL_MAP: typing.Dict[str, typing.Type[Shell]] = {
    "ipy": IPythonShell,
    "ipython": IPythonShell,
    "bpy": BPythonShell,
    "bpython": BPythonShell,
    "bpyc": BPythonCursesShell,
    "bpython-curses": BPythonCursesShell,
    "py": PythonShell,
    "python": PythonShell,
    "auto": AutoShell,
    "ptpy": PtPythonShell,
    "ptpython": PtPythonShell,
    "ptipy": PtIPythonShell,
    "ptipython": PtIPythonShell,
}


# _cfg and _config_registry are singletons that may be mutated in a .konchrc file
_cfg = Config()
_config_registry = {"default": _cfg}


def start(
    context: typing.Optional[typing.Mapping] = None,
    banner: typing.Optional[str] = None,
    shell: typing.Type[Shell] = AutoShell,
    prompt: typing.Optional[str] = None,
    output: typing.Optional[str] = None,
    context_format: str = "full",
    **kwargs: typing.Any,
) -> None:
    """Start up the konch shell. Takes the same parameters as Shell.__init__."""
    logger.debug(f"Using shell: {shell!r}")
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
        **kwargs,
    ).start()


def config(config_dict: typing.Mapping) -> Config:
    """Configures the konch shell. This function should be called in a
    .konchrc file.

    :param dict config_dict: Dict that may contain 'context', 'banner', and/or
        'shell' (default shell class to use).
    """
    logger.debug(f"Updating with {config_dict}")
    _cfg.update(config_dict)
    return _cfg


def named_config(name: str, config_dict: typing.Mapping) -> None:
    """Adds a named config to the config registry. The first argument
    may either be a string or a collection of strings.

    This function should be called in a .konchrc file.
    """
    names = (
        name
        if isinstance(name, Iterable) and not isinstance(name, (str, bytes))
        else [name]
    )
    for each in names:
        _config_registry[each] = Config(**config_dict)


def reset_config() -> Config:
    global _cfg
    _cfg = Config()
    return _cfg


def __ensure_directory_in_path(filename: Path) -> None:
    """Ensures that a file's directory is in the Python path."""
    directory = Path(filename).parent.resolve()
    if directory not in sys.path:
        logger.debug(f"Adding {directory} to sys.path")
        sys.path.insert(0, str(directory))


CONFIG_FILE = Path(".konchrc")
for DEFAULT_CONFIG_FILE in (
    Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    / "konchrc.default",
    Path.home() / ".konchrc.default",
):
    if DEFAULT_CONFIG_FILE.exists():
        break

SEPARATOR = f"\n{'*' * 46}\n"


def confirm(text: str, default: bool = False) -> bool:
    """Display a confirmation prompt."""
    choices = "Y/n" if default else "y/N"
    prompt = f"{style(text, bold=True)} [{choices}]: "
    while 1:
        try:
            print(prompt, end="")
            value = input("").lower().strip()
        except (KeyboardInterrupt, EOFError):
            sys.exit(1)
        if value in ("y", "yes"):
            rv = True
        elif value in ("n", "no"):
            rv = False
        elif value == "":
            rv = default
        else:
            print_error("Error: invalid input")
            continue
        break
    return rv


def use_file(
    filename: typing.Union[Path, str, None], trust: bool = False
) -> typing.Union[types.ModuleType, None]:
    """Load filename as a python file. Import ``filename`` and return it
    as a module.
    """
    config_file = filename or resolve_path(CONFIG_FILE)

    def preview_unauthorized() -> None:
        if not config_file:
            return None
        print(SEPARATOR, file=sys.stderr)
        with Path(config_file).open("r", encoding="utf-8") as fp:
            for line in fp:
                print(line, end="", file=sys.stderr)
        print(SEPARATOR, file=sys.stderr)

    if config_file and not Path(config_file).exists():
        print_error(f'"{filename}" not found.')
        sys.exit(1)
    if config_file and Path(config_file).exists():
        if not trust:
            with AuthFile.load() as authfile:
                try:
                    authfile.check(Path(config_file))
                except KonchrcChangedError:
                    print_error(f'"{config_file}" has changed since you last used it.')
                    preview_unauthorized()
                    if confirm("Would you like to authorize it?"):
                        authfile.allow(Path(config_file))
                        print()
                    else:
                        sys.exit(1)
                except KonchrcNotAuthorizedError:
                    print_error(f'"{config_file}" is blocked.')
                    preview_unauthorized()
                    if confirm("Would you like to authorize it?"):
                        authfile.allow(Path(config_file))
                        print()
                    else:
                        sys.exit(1)

        logger.info(f"Using {config_file}")
        # Ensure that relative imports are possible
        __ensure_directory_in_path(Path(config_file))
        mod = None
        try:
            mod = SourceFileLoader("konchrc", str(config_file)).load_module("konchrc")
        except UnboundLocalError:  # File not found
            pass
        except NoNameError as error:
            print_error(
                f"Object {error.obj} in `context` has no __name__ attribute. "
                "Use a context dictionary instead."
            )
            sys.exit(1)
        else:
            return mod
    if not config_file:
        print_warning("No konch config file found.")
    else:
        print_warning(f'"{config_file}" not found.')
    return None


def resolve_path(filename: Path) -> typing.Union[Path, None]:
    """Find a file by walking up parent directories until the file is found.
    Return the absolute path of the file.
    """
    current = Path.cwd()
    # Stop search at home directory
    sentinel_dir = Path.home().parent.resolve()
    while current != sentinel_dir:
        target = Path(current) / Path(filename)
        if target.exists():
            return target.resolve()
        else:
            current = current.parent.resolve()

    return None


def get_editor() -> str:
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


def edit_file(
    filename: typing.Optional[Path], editor: typing.Optional[str] = None
) -> None:
    if not filename:
        print_error("filename not passed.")
        sys.exit(1)
    editor = editor or get_editor()
    try:
        result = subprocess.Popen(f'{editor} "{filename}"', shell=True)
        exit_code = result.wait()
        if exit_code != 0:
            print_error(f"{editor}: Editing failed!")
            sys.exit(1)
    except OSError as err:
        print_error(f"{editor}: Editing failed: {err}")
        sys.exit(1)
    else:
        with AuthFile.load() as authfile:
            authfile.allow(filename)


INIT_TEMPLATE = """# vi: set ft=python :
import konch
import sys
import os

# Available options:
#   "context", "banner", "shell", "prompt", "output",
#   "context_format", "ipy_extensions", "ipy_autoreload",
#   "ipy_colors", "ipy_highlighting_style", "ptpy_vi_mode"
# See: https://konch.readthedocs.io/en/latest/#configuration
konch.config({
    "context": [
        sys,
        os,
    ]
})


def setup():
    pass


def teardown():
    pass
"""


def init_config(config_file: Path) -> typing.NoReturn:
    if not config_file.exists():
        print(f'Writing to "{config_file.resolve()}"...')
        print(SEPARATOR)
        print(INIT_TEMPLATE, end="")
        print(SEPARATOR)
        init_template = INIT_TEMPLATE
        if DEFAULT_CONFIG_FILE.exists():
            with Path(DEFAULT_CONFIG_FILE).open("r") as fp:
                init_template = fp.read()
        with Path(config_file).open("w") as fp:
            fp.write(init_template)
        with AuthFile.load() as authfile:
            authfile.allow(config_file)

        relpath = _relpath(config_file)
        is_default = relpath == Path(CONFIG_FILE)
        edit_cmd = "konch edit" if is_default else f"konch edit {relpath}"
        run_cmd = "konch" if is_default else f"konch -f {relpath}"
        print(f"{style('Done!', GREEN)} ✨ 🐚 ✨")
        print(f"To edit your config: `{style(edit_cmd, bold=True)}`")
        print(f"To start the shell:  `{style(run_cmd, bold=True)}`")
        sys.exit(0)
    else:
        print_error(f'"{config_file}" already exists in this directory.')
        sys.exit(1)


def edit_config(
    config_file: typing.Optional[Path] = None, editor: typing.Optional[str] = None
) -> typing.NoReturn:
    filename = config_file or resolve_path(CONFIG_FILE)
    if not filename:
        print_error('No ".konchrc" file found.')
        styled_cmd = style("konch init", bold=True, file=sys.stderr)
        print(f"Run `{styled_cmd}` to create it.", file=sys.stderr)
        sys.exit(1)
    if not filename.exists():
        print_error(f'"{filename}" does not exist.')
        relpath = _relpath(filename)
        is_default = relpath == Path(CONFIG_FILE)
        cmd = "konch init" if is_default else f"konch init {filename}"
        styled_cmd = style(cmd, bold=True, file=sys.stderr)
        print(f"Run `{styled_cmd}` to create it.", file=sys.stderr)
        sys.exit(1)
    print(f'Editing file: "{filename}"')
    edit_file(filename, editor=editor)
    sys.exit(0)


def allow_config(config_file: typing.Optional[Path] = None) -> typing.NoReturn:
    filename: typing.Union[Path, None]
    if config_file and config_file.is_dir():
        filename = Path(config_file) / CONFIG_FILE
    else:
        filename = config_file or resolve_path(CONFIG_FILE)
    if not filename:
        print_error("No config file found.")
        sys.exit(1)
    with AuthFile.load() as authfile:
        if authfile.check(filename, raise_error=False):
            print_warning(f'"{filename}" is already authorized.')
        else:
            try:
                print(f'Authorizing "{filename}"...')
                authfile.allow(filename)
            except FileNotFoundError:
                print_error(f'"{filename}" does not exist.')
                sys.exit(1)
        print(f"{style('Done!', GREEN)} ✨ 🐚 ✨")
        relpath = _relpath(filename)
        cmd = "konch" if relpath == Path(CONFIG_FILE) else f"konch -f {relpath}"
        print(f"You can now start a shell with `{style(cmd, bold=True)}`.")
    sys.exit(0)


def deny_config(config_file: typing.Optional[Path] = None) -> typing.NoReturn:
    filename: typing.Union[Path, None]
    if config_file and config_file.is_dir():
        filename = Path(config_file) / CONFIG_FILE
    else:
        filename = config_file or resolve_path(CONFIG_FILE)
    if not filename:
        print_error("No config file found.")
        sys.exit(1)
    print(f'Removing authorization for "{filename}"...')
    with AuthFile.load() as authfile:
        try:
            authfile.deny(filename)
        except FileNotFoundError:
            print_error(f'"{filename}" does not exist.')
            sys.exit(1)
        else:
            print(style("Done!", GREEN))
    sys.exit(0)


def parse_args(argv: typing.Optional[typing.Sequence] = None) -> typing.Dict[str, str]:
    """Exposes the docopt command-line arguments parser.
    Return a dictionary of arguments.
    """
    return docopt(__doc__, argv=argv, version=__version__)


def main(argv: typing.Optional[typing.Sequence] = None) -> typing.NoReturn:
    """Main entry point for the konch CLI."""
    args = parse_args(argv)

    if args["--debug"]:
        logging.basicConfig(
            format="%(levelname)s %(filename)s: %(message)s", level=logging.DEBUG
        )
    logger.debug(args)

    config_file: typing.Union[Path, None]
    if args["init"]:
        config_file = Path(args["<config_file>"] or CONFIG_FILE)
        init_config(config_file)
    else:
        config_file = Path(args["<config_file>"]) if args["<config_file>"] else None
        if args["edit"]:
            edit_config(config_file)
        elif args["allow"]:
            allow_config(config_file)
        elif args["deny"]:
            deny_config(config_file)

    mod = use_file(Path(args["--file"]) if args["--file"] else None)
    if hasattr(mod, "setup"):
        mod.setup()  # type: ignore

    if args["--name"]:
        if args["--name"] not in _config_registry:
            print_error(f'Invalid --name: "{args["--name"]}"')
            sys.exit(1)
        config_dict = _config_registry[args["--name"]]
        logger.debug(f'Using named config: "{args["--name"]}"')
        logger.debug(config_dict)
    else:
        config_dict = _cfg
    # Allow default shell to be overriden by command-line argument
    shell_name = args["--shell"]
    if shell_name:
        config_dict["shell"] = SHELL_MAP.get(shell_name.lower(), AutoShell)
    logger.debug(f"Starting with config {config_dict}")
    start(**config_dict)

    if hasattr(mod, "teardown"):
        mod.teardown()  # type: ignore
    sys.exit(0)


if __name__ == "__main__":
    main()
