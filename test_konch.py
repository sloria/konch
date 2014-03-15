# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import sys
import os

import pytest
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


def test_default_make_banner():
    result = konch.make_banner()
    assert sys.version in result
    assert konch.DEFAULT_BANNER_TEXT in result


def test_make_banner_custom():
    text = 'I want to be the very best'
    result = konch.make_banner(text)
    assert text in result
    assert sys.version in result


def test_make_banner_with_context():
    context = {'foo': 42}
    result = konch.make_banner(context=context)
    assert konch.format_context(context) in result


def test_cfg_defaults():
    assert konch.cfg['shell'] == konch.AutoShell
    assert konch.cfg['banner'] is None
    assert konch.cfg['context'] == {}


def test_config():
    assert konch.cfg == konch.Config()
    konch.config({
        'banner': 'Foo bar'
    })
    assert konch.cfg['banner'] == 'Foo bar'


def test_reset_config():
    assert konch.cfg == konch.Config()
    konch.config({
        'banner': 'Foo bar'
    })
    konch.reset_config()
    assert konch.cfg == konch.Config()


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
    assert konch.cfg == konch.Config()
    def my_func():
        return
    konch.config({
        'context': [my_func]
    })
    assert konch.cfg['context']['my_func'] == my_func


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


##### Command tests #####


def test_init_creates_config_file(env):
    res = env.run('konch', 'init')
    assert res.returncode == 0
    assert konch.DEFAULT_CONFIG_FILE in res.files_created


def test_init_with_filename(env):
    res = env.run('konch', 'init', 'myconfig')
    assert 'myconfig' in res.files_created


def test_konch_with_no_config_file(env):
    res = env.run('konch', expect_stderr=True)
    assert res.returncode == 0


def test_konch_init_when_config_file_exists(env):
    env.run('konch', 'init')
    res = env.run('konch', 'init', expect_error=True)
    assert 'already exists' in res.stdout
    assert res.returncode == 1


def test_default_banner(env):
    env.run('konch', 'init')
    res = env.run('konch', expect_stderr=True)
    # In virtualenvs, banners output to stderr
    assert_in_output(konch.DEFAULT_BANNER_TEXT, res)
    assert_in_output(str(sys.version), res)


def test_config_file_not_found(env):
    res = env.run('konch', '-f', 'notfound', expect_stderr=True)
    assert 'not found' in res.stderr
    assert res.returncode == 0

TEST_CONFIG = """
import konch

konch.config({
    'banner': 'Test banner'
})
"""


def test_custom_banner(env):
    with open(os.path.join(env.base_path, 'testrc'), 'w') as fp:
        fp.write(TEST_CONFIG)
    res = env.run('konch', '-f', 'testrc', expect_stderr=True)
    assert_in_output('Test banner', res)


def test_version(env):
    res = env.run('konch', '--version')
    assert konch.__version__ in res.stdout
    res = env.run('konch', '-v')
    assert konch.__version__ in res.stdout


