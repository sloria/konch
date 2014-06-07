# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import sys
import os

import pytest
from docopt import DocoptExit
from scripttest import TestFileEnvironment

import konch


def assert_in_output(s, res, message=None):
    """Assert that a string is in either stdout or std err.
    Included because banners are sometimes outputted to stderr.
    """
    assert any([s in res.stdout, res.stdout, s in res.stderr]), message


@pytest.fixture
def env():
    return TestFileEnvironment(ignore_hidden=False)


def teardown_function(func):
    konch.reset_config()


def test_format_context():
    context = {
        'my_number': 42,
        'my_func': lambda x: x,
    }
    result = konch.format_context(context)
    assert result == '\n'.join([
        '{0}: {1!r}'.format(key, value)
        for key, value in context.items()
    ])


def test_make_banner_custom():
    text = 'I want to be the very best'
    result = konch.make_banner(text)
    assert text in result
    assert sys.version in result


def test_make_banner_with_context():
    context = {'foo': 42}
    result = konch.make_banner(context=context)
    assert konch.format_context(context) in result


def test_make_banner_hide_context():
    context = {'foo': 42}
    result = konch.make_banner(context=context, hide_context=True)
    assert konch.format_context(context) not in result


def test_cfg_defaults():
    assert konch._cfg['shell'] == konch.AutoShell
    assert konch._cfg['banner'] is None
    assert konch._cfg['context'] == {}
    assert konch._cfg['hide_context'] is False


def test_config():
    assert konch._cfg == konch.Config()
    konch.config({
        'banner': 'Foo bar'
    })
    assert konch._cfg['banner'] == 'Foo bar'


def test_reset_config():
    assert konch._cfg == konch.Config()
    konch.config({
        'banner': 'Foo bar'
    })
    konch.reset_config()
    assert konch._cfg == konch.Config()


def test_parse_args():
    try:
        args = konch.parse_args()
        assert '--shell' in args
        assert 'init' in args
        assert '<config_file>' in args
        assert '--name' in args
    except DocoptExit:
        pass


def test_context_list2dict():
    import math
    class MyClass:
        pass
    def my_func():
        pass

    my_objects = [math, MyClass, my_func]
    expected = {'my_func': my_func, 'MyClass': MyClass, 'math': math}
    assert konch.context_list2dict(my_objects) == expected


def test_config_list():
    assert konch._cfg == konch.Config()
    def my_func():
        return
    konch.config({
        'context': [my_func]
    })
    assert konch._cfg['context']['my_func'] == my_func


def test_config_converts_list_context():
    import math
    config = konch.Config(context=[math])
    assert config['context'] == {'math': math}


def test_config_set_context_converts_list():
    import math
    config = konch.Config()
    config['context'] = [math]
    assert config['context'] == {'math': math}


def test_config_update_context_converts_list():
    import math
    config = konch.Config()
    config.update({
        'context': [math]
    })
    assert config['context'] == {'math': math}


def test_named_config_adds_to_registry():
    assert konch._config_registry['default'] == konch._cfg
    assert len(konch._config_registry.keys()) == 1
    konch.named_config('mynamespace', {'context': {'foo': 42}})
    assert len(konch._config_registry.keys()) == 2
    # reset config_registry
    konch._config_registry = {'default': konch._cfg}


##### Command tests #####


def test_init_creates_config_file(env):
    res = env.run('konch', 'init')
    assert res.returncode == 0
    assert konch.DEFAULT_CONFIG_FILE in res.files_created


def test_init_with_filename(env):
    res = env.run('konch', 'init', 'myconfig')
    assert 'myconfig' in res.files_created


def test_konch_with_no_config_file(env):
    try:
        os.remove(os.path.join(env.base_path, '.konchrc'))
    except OSError:
        pass
    res = env.run('konch', expect_stderr=True)
    assert res.returncode == 0


def test_konch_init_when_config_file_exists(env):
    env.run('konch', 'init')
    res = env.run('konch', 'init', expect_error=True)
    assert 'already exists' in res.stderr
    assert res.returncode == 1


def test_default_banner(env):
    env.run('konch', 'init')
    res = env.run('konch', expect_stderr=True)
    assert_in_output(str(sys.version), res)


def test_config_file_not_found(env):
    res = env.run('konch', '-f', 'notfound', expect_stderr=True)
    assert 'not found' in res.stderr
    assert res.returncode == 0

TEST_CONFIG = """
import konch

konch.config({
    'banner': 'Test banner'
    'prompt': 'myprompt >>>'
})
"""


@pytest.fixture
def fileenv(request, env):
    fpath = os.path.join(env.base_path, 'testrc')
    with open(fpath, 'w') as fp:
        fp.write(TEST_CONFIG_WITH_NAMES)
    def finalize():
        os.remove(fpath)
    request.addfinalizer(finalize)
    return env


def test_custom_banner(fileenv):
    res = fileenv.run('konch', '-f', 'testrc', expect_stderr=True)
    assert_in_output('Test banner', res)


def test_custom_prompt(fileenv):
    res = fileenv.run('konch', '-f', 'testrc', expect_stderr=True)
    assert_in_output('myprompt >>>', res)


def test_version(env):
    res = env.run('konch', '--version')
    assert konch.__version__ in res.stdout
    res = env.run('konch', '-v')
    assert konch.__version__ in res.stdout


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
"""


@pytest.fixture
def fileenv2(request, env):
    fpath = os.path.join(env.base_path, '.konchrc')
    with open(fpath, 'w') as fp:
        fp.write(TEST_CONFIG_WITH_NAMES)
    def finalize():
        os.remove(fpath)
    request.addfinalizer(finalize)
    return env


@pytest.fixture
def folderenv(request, env):
    folder = os.path.abspath(os.path.join(env.base_path, 'testdir'))
    os.makedirs(folder)
    def finalize():
        os.removedirs(folder)
    request.addfinalizer(finalize)
    return env


def test_default_config(fileenv2):
    res = fileenv2.run('konch', expect_stderr=True)
    assert_in_output('Default', res)
    assert_in_output('foo', res)


def test_selecting_named_config(fileenv2):
    res = fileenv2.run('konch', '-n', 'conf2', expect_stderr=True)
    assert_in_output('Conf2', res)
    assert_in_output('bar', res)


def test_selecting_name_that_doesnt_exist(fileenv2):
    res = fileenv2.run('konch', '-n', 'doesntexist', expect_stderr=True)
    assert_in_output('Default', res)


def test_resolve_path(folderenv):
    folderenv.run('konch', 'init')
    fpath = os.path.abspath(os.path.join(folderenv.base_path, '.konchrc'))
    assert os.path.exists(fpath)
    folder = os.path.abspath(os.path.join(folderenv.base_path, 'testdir'))
    os.chdir(folder)
    assert konch.resolve_path('.konchrc') == fpath
