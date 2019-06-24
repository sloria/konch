from __future__ import unicode_literals
import sys
from pathlib import Path
import os

import pytest
from docopt import DocoptExit
from scripttest import TestFileEnvironment as FileEnvironment

import konch


try:
    import ptpython  # noqa: F401
except ImportError:
    HAS_PTPYTHON = False
else:
    HAS_PTPYTHON = True


def assert_in_output(s, res, message=None):
    """Assert that a string is in either stdout or std err.
    Included because banners are sometimes outputted to stderr.
    """
    assert any([s in res.stdout, s in res.stderr]), message or f"{s} not in output"


@pytest.fixture
def env():
    env_ = FileEnvironment(ignore_hidden=False)
    auth_file = Path(env_.base_path) / "konch_auth"
    env_.environ["KONCH_AUTH_FILE"] = str(auth_file)
    env_.environ["KONCH_EDITOR"] = "echo"
    yield env_
    try:
        auth_file.unlink()
    except FileNotFoundError:
        pass


def teardown_function(func):
    konch.reset_config()


def test_make_banner_custom():
    text = "I want to be the very best"
    result = konch.make_banner(text)
    assert text in result
    assert sys.version in result


def test_full_formatter():
    class Foo:
        def __repr__(self):
            return "<Foo>"

    context = {"foo": Foo(), "bar": 42}

    assert (
        konch.format_context(context, formatter="full")
        == "\nContext:\nbar: 42\nfoo: <Foo>"
    )


def test_short_formatter():
    class Foo:
        def __repr__(self):
            return "<Foo>"

    context = {"foo": Foo(), "bar": 42}

    assert konch.format_context(context, formatter="short") == "\nContext:\nbar, foo"


def test_custom_formatter():
    context = {"foo": 42, "bar": 24}

    def my_formatter(ctx):
        return "*".join(sorted(ctx.keys()))

    assert konch.format_context(context, formatter=my_formatter) == "bar*foo"


def test_make_banner_includes_full_context_by_default():
    context = {"foo": 42}
    result = konch.make_banner(context=context)
    assert konch.format_context(context, formatter="full") in result


def test_make_banner_hide_context():
    context = {"foo": 42}
    result = konch.make_banner(context=context, context_format="hide")
    assert konch.format_context(context) not in result


def test_make_banner_custom_format():
    context = {"foo": 42}
    result = konch.make_banner(context=context, context_format=lambda ctx: repr(ctx))
    assert repr(context) in result


def test_cfg_defaults():
    assert konch._cfg["shell"] == konch.AutoShell
    assert konch._cfg["banner"] is None
    assert konch._cfg["context"] == {}
    assert konch._cfg["context_format"] == "full"


def test_config():
    assert konch._cfg == konch.Config()
    konch.config({"banner": "Foo bar"})
    assert konch._cfg["banner"] == "Foo bar"


def test_reset_config():
    assert konch._cfg == konch.Config()
    konch.config({"banner": "Foo bar"})
    konch.reset_config()
    assert konch._cfg == konch.Config()


def test_parse_args():
    try:
        args = konch.parse_args()
        assert "--shell" in args
        assert "init" in args
        assert "<config_file>" in args
        assert "--name" in args
    except DocoptExit:
        pass


def test_context_list2dict():
    import math
    from logging import config

    class MyClass:
        pass

    def my_func():
        pass

    my_objects = [math, MyClass, my_func, config]
    expected = {"my_func": my_func, "MyClass": MyClass, "math": math, "config": config}
    assert konch.context_list2dict(my_objects) == expected


def test_config_list():
    assert konch._cfg == konch.Config()

    def my_func():
        return

    konch.config({"context": [my_func]})
    assert konch._cfg["context"]["my_func"] == my_func


def test_config_converts_list_context():
    import math

    config = konch.Config(context=[math])
    assert config["context"] == {"math": math}


def test_config_set_context_converts_list():
    import math

    config = konch.Config()
    config["context"] = [math]
    assert config["context"] == {"math": math}


def test_config_update_context_converts_list():
    import math

    config = konch.Config()
    config.update({"context": [math]})
    assert config["context"] == {"math": math}


def test_config_shallow_merges_context():
    config = konch.Config()
    config.update({"context": {"foo": 42}, "banner": "bar"})
    config.update({"context": {"baz": 24}, "banner": "qux"})

    assert config["context"] == {"foo": 42, "baz": 24}
    assert config["banner"] == "qux"

    config = konch.Config()
    config.update({"context": {"foo": 42}})
    config.update({"context": {"foo": 24}})
    assert config["context"] == {"foo": 24}

    config = konch.Config()
    config.update({"context": {"foo": {"inner": 42}}})
    config.update({"context": {"foo": {"inner2": 24}}})
    assert config["context"] == {"foo": {"inner2": 24}}

    config = konch.Config()

    def bar():
        pass

    config.update({"context": {"foo": 42}, "banner": "bar"})
    config.update({"context": [bar], "banner": "bar"})


def test_named_config_adds_to_registry():
    assert konch._config_registry["default"] == konch._cfg
    assert len(konch._config_registry.keys()) == 1
    konch.named_config("mynamespace", {"context": {"foo": 42}})
    assert len(konch._config_registry.keys()) == 2
    # reset config_registry
    konch._config_registry = {"default": konch._cfg}


def test_context_can_be_callable():
    def get_context():
        return {"foo": 42}

    shell = konch.Shell(context=get_context)

    assert shell.context == {"foo": 42}


##### Command tests #####


def test_init_creates_config_file(env):
    res = env.run("konch", "init")
    assert res.returncode == 0
    assert str(konch.CONFIG_FILE) in res.files_created


def test_init_with_filename(env):
    res = env.run("konch", "init", "myconfig")
    assert "myconfig" in res.files_created


def test_konch_init_when_config_file_exists(env):
    env.run("konch", "init")
    res = env.run("konch", "init", expect_error=True)
    assert "already exists" in res.stderr
    assert res.returncode == 1


def test_file_blocked(env, request):
    env.writefile(".konchrc", content=b"givemeyourbitcoinz")
    request.addfinalizer(lambda: (Path(env.base_path) / ".konchrc").unlink())
    res = env.run("konch", expect_stderr=True, expect_error=True)
    assert "blocked" in res.stderr
    assert res.returncode == 1


def test_edit(env, request):
    env.run("konch", "init")
    res = env.run("konch", "edit")
    assert res.returncode == 0
    assert "Editing file" in res.stdout


def test_edit_file_not_found(env, request):
    res = env.run("konch", "edit", "notfound", expect_error=True)
    assert res.returncode == 1
    assert "ERROR" in res.stderr
    assert "konch init" in res.stderr


@pytest.mark.skipif(HAS_PTPYTHON, reason="test incompatible with ptpython")
def test_edit_with_filename(env, request):
    env.run("konch", "init", "myfile")
    res = env.run("konch", "edit", "myfile")
    assert res.returncode == 0
    assert "Editing file" in res.stdout

    # File is automatically allowed
    res = env.run("konch", "-f", "myfile")
    assert res.returncode == 0


@pytest.mark.skipif(HAS_PTPYTHON, reason="test incompatible with ptpython")
def test_allow_file(env, request):
    env.writefile(".konchrc", content=b"import konch")
    request.addfinalizer(lambda: (Path(env.base_path) / ".konchrc").unlink())
    env.run("konch", "allow")
    res = env.run("konch")
    assert res.returncode == 0


@pytest.mark.skipif(HAS_PTPYTHON, reason="test incompatible with ptpython")
def test_allow_specified_file(env, request):
    env.writefile("mykonchrc", content=b"import konch")
    request.addfinalizer(lambda: (Path(env.base_path) / "mykonchrc").unlink())

    res = env.run("konch", "-f", "mykonchrc", expect_error=True)
    assert res.returncode == 1

    env.run("konch", "allow", "mykonchrc")
    res = env.run("konch", "-f", "mykonchrc", expect_error=False)
    assert res.returncode == 0


@pytest.mark.skipif(HAS_PTPYTHON, reason="test incompatible with ptpython")
def test_allow_file_not_found(env, request):
    res = env.run("konch", "allow", "notfound", expect_stderr=True, expect_error=True)
    assert "does not exist" in res.stderr
    assert res.returncode == 1


@pytest.mark.skipif(HAS_PTPYTHON, reason="test incompatible with ptpython")
def test_file_blocked_if_changed(env, request):
    env.writefile(".konchrc", content=b"import konch")
    request.addfinalizer(lambda: (Path(env.base_path) / ".konchrc").unlink())
    env.run("konch", "allow")
    res = env.run("konch")
    assert res.returncode == 0

    env.writefile(".konchrc", content=b"import konch as k")
    res = env.run("konch", expect_stderr=True, expect_error=True)
    assert "changed" in res.stderr
    assert res.returncode == 1


@pytest.mark.skipif(HAS_PTPYTHON, reason="test incompatible with ptpython")
def test_deny_file(env, request):
    env.writefile(".konchrc", content=b"import konch")
    request.addfinalizer(lambda: (Path(env.base_path) / ".konchrc").unlink())
    env.run("konch", "allow")
    res = env.run("konch")
    assert res.returncode == 0

    env.run("konch", "deny")
    res = env.run("konch", expect_stderr=True, expect_error=True)
    assert "blocked" in res.stderr
    assert res.returncode == 1


@pytest.mark.skipif(HAS_PTPYTHON, reason="test incompatible with ptpython")
def test_deny_file_not_found(env, request):
    res = env.run("konch", "deny", "notfound", expect_stderr=True, expect_error=True)
    assert "does not exist" in res.stderr
    assert res.returncode == 1


@pytest.mark.skipif(HAS_PTPYTHON, reason="test incompatible with ptpython")
def test_default_banner(env):
    env.run("konch", "init")
    res = env.run("konch", expect_stderr=True)
    assert_in_output(str(sys.version), res)


@pytest.mark.skipif(HAS_PTPYTHON, reason="test incompatible with ptpython")
def test_config_file_not_found(env):
    res = env.run("konch", "-f", "notfound", expect_stderr=True, expect_error=True)
    assert '"notfound" not found' in res.stderr
    assert res.returncode == 1


TEST_CONFIG = """
import konch

konch.config({
    'banner': 'Test banner',
    'prompt': 'myprompt >>>'
})
"""


@pytest.fixture
def fileenv(request, env):
    fpath = Path(env.base_path) / "testrc"
    with fpath.open("w") as fp:
        fp.write(TEST_CONFIG)

    env.run("konch", "allow", fpath)
    yield env
    fpath.unlink()


@pytest.mark.skipif(HAS_PTPYTHON, reason="test incompatible with ptpython")
def test_custom_banner(fileenv):
    res = fileenv.run("konch", "-f", "testrc", expect_stderr=True)
    assert_in_output("Test banner", res)


# TODO: Get this test working with IPython
def test_custom_prompt(fileenv):
    res = fileenv.run("konch", "-f", "testrc", "-s", "py", expect_stderr=True)
    assert_in_output("myprompt >>>", res)


def test_version(env):
    res = env.run("konch", "--version")
    assert konch.__version__ in res.stdout
    res = env.run("konch", "-v")
    assert konch.__version__ in res.stdout


def test_nonblank_context(env):
    env.run("konch", "init")
    res = env.run("python", "-m", "konch", expect_stderr=True)
    assert "<module 'sys'" in res.stdout


TEST_CONFIG_WITH_NAMES = """
import konch

konch.config({
    'context': {
        'foo': 42,
    },
    'banner': 'Default'
})

konch.named_config('conf2', {
    'context': {
        'bar': 24
    },
    'banner': 'Conf2'
})

konch.named_config(['conf3', 'c3'], {
    'context': {
        'baz': 424,
    },
    'banner': 'Conf3',
})
"""


TEST_CONFIG_WITH_SETUP_AND_TEARDOWN = """
import konch

def setup():
    print('setup!')

def teardown():
    print('teardown!')
"""

TEST_CONFIG_WITH_NAMELESS_OBJECT = """
import konch

nameless = object()

konch.config({
    'context': [nameless]
})
"""


TEST_CONFIG_UNCHANGED_KONCHRC = """
import konch
import sys

konch.config({
    'context': [sys]
})
"""


@pytest.fixture
def names_env(request, env):
    fpath = Path(env.base_path) / ".konchrc"
    with fpath.open("w") as fp:
        fp.write(TEST_CONFIG_WITH_NAMES)

    env.run("konch", "allow", fpath)
    yield env
    fpath.unlink()


@pytest.fixture
def setup_env(request, env):
    fpath = Path(env.base_path) / ".konchrc"
    with fpath.open("w") as fp:
        fp.write(TEST_CONFIG_WITH_SETUP_AND_TEARDOWN)

    env.run("konch", "allow", fpath)
    yield env
    fpath.unlink()


@pytest.fixture
def nameless_env(request, env):
    fpath = Path(env.base_path) / ".konchrc"
    with fpath.open("w") as fp:
        fp.write(TEST_CONFIG_WITH_NAMELESS_OBJECT)

    env.run("konch", "allow", fpath)
    yield env
    fpath.unlink()


@pytest.fixture
def old_konchrc_env(request, env):
    fpath = Path(env.base_path) / ".konchrc"
    with fpath.open("w") as fp:
        fp.write(TEST_CONFIG_UNCHANGED_KONCHRC)

    env.run("konch", "allow", fpath)
    yield env
    fpath.unlink()


@pytest.fixture
def folderenv(request, env):
    folder = (Path(env.base_path) / "testdir").resolve()
    folder.mkdir(parents=True)
    yield env
    folder.rmdir()


@pytest.mark.skipif(HAS_PTPYTHON, reason="test incompatible with ptpython")
def test_default_config(names_env):
    res = names_env.run("konch", expect_stderr=True)
    assert_in_output("Default", res)
    assert_in_output("foo", res)


@pytest.mark.skipif(HAS_PTPYTHON, reason="test incompatible with ptpython")
def test_setup_teardown(setup_env):
    res = setup_env.run("konch", expect_stderr=True)
    assert_in_output("setup!", res)
    assert_in_output("teardown!", res)


@pytest.mark.skipif(HAS_PTPYTHON, reason="test incompatible with ptpython")
def test_selecting_named_config(names_env):
    res = names_env.run("konch", "-n", "conf2", expect_stderr=True)
    assert_in_output("Conf2", res)
    assert_in_output("bar", res)


@pytest.mark.skipif(HAS_PTPYTHON, reason="test incompatible with ptpython")
def test_named_config_with_multiple_names(names_env):
    res = names_env.run("konch", "-n", "conf3", expect_stderr=True)
    assert_in_output("Conf3", res)
    assert_in_output("baz", res)

    res = names_env.run("konch", "-n", "c3", expect_stderr=True)
    assert_in_output("Conf3", res)
    assert_in_output("baz", res)


@pytest.mark.skipif(HAS_PTPYTHON, reason="test incompatible with ptpython")
def test_selecting_name_that_doesnt_exist(names_env):
    res = names_env.run("konch", "-n", "doesntexist", expect_error=True)
    assert res.returncode == 1
    assert "Invalid --name" in res.stderr


# Regression test for https://github.com/sloria/konch/issues/105
@pytest.mark.skipif(HAS_PTPYTHON, reason="test incompatible with ptpython")
def test_context_list_with_nameless_object_returns_error(nameless_env):
    res = nameless_env.run("konch", expect_error=True)
    assert res.returncode == 1
    assert "has no __name__" in res.stderr
    assert "Use a context dictionary instead" in res.stderr


@pytest.mark.skipif(HAS_PTPYTHON, reason="test incompatible with ptpython")
def test_unchanged_konchrc(old_konchrc_env):
    res = old_konchrc_env.run("konch", expect_stderr=True)
    assert "<module 'sys'" in res.stdout


def test_resolve_path(folderenv):
    folderenv.run("konch", "init")
    fpath = (Path(folderenv.base_path) / ".konchrc").resolve()
    assert fpath.exists()
    folder = (Path(folderenv.base_path) / "testdir").resolve()
    os.chdir(folder)
    assert konch.resolve_path(".konchrc") == fpath


class TestAuthFile:
    @pytest.fixture()
    def auth_file(self, env):
        auth_filepath = Path(env.base_path) / "konch_auth"
        env.writefile(auth_filepath, content=b"")
        yield auth_filepath
        auth_filepath.unlink()

    @pytest.fixture()
    def rcfile(self, env):
        filepath = Path(env.base_path) / ".konchrc"
        env.writefile(filepath, content=b"import konch")
        yield filepath
        filepath.unlink()

    def test_check_returns_true_if_authorized(self, auth_file, rcfile):
        with konch.AuthFile.load(auth_file) as authfile:
            authfile.allow(rcfile)
            assert authfile.check(rcfile) is True

    def test_deny(self, auth_file, rcfile):
        with konch.AuthFile.load(auth_file) as authfile:
            authfile.allow(rcfile)
            assert authfile.check(rcfile)
            authfile.deny(rcfile)
            with pytest.raises(konch.KonchrcNotAuthorizedError):
                authfile.check(rcfile)

    def test_check_raises_if_file_not_authorized(self, auth_file, rcfile):
        with konch.AuthFile.load(auth_file) as authfile:
            with pytest.raises(konch.KonchrcNotAuthorizedError):
                authfile.check(rcfile)

    def test_check_does_not_raise_if_file_not_authorized_and_raise_error_false(
        self, auth_file, rcfile
    ):
        with konch.AuthFile.load(auth_file) as authfile:
            assert authfile.check(rcfile, raise_error=False) is False

    def test_check_raises_if_file_changed(self, auth_file, rcfile, env):
        with konch.AuthFile.load(auth_file) as authfile:
            authfile.allow(rcfile)
            assert authfile.check(rcfile)
            env.writefile(rcfile, content=b"changed")
            with pytest.raises(konch.KonchrcChangedError):
                authfile.check(rcfile)

    def test_check_does_not_raise_if_file_changed_and_raise_error_false(
        self, auth_file, rcfile, env
    ):
        with konch.AuthFile.load(auth_file) as authfile:
            authfile.allow(rcfile)
            assert authfile.check(rcfile)
            env.writefile(rcfile, content=b"changed")
            assert authfile.check(rcfile, raise_error=False) is False
