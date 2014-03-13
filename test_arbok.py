# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import sys

import arbok


def teardown_function(func):
    arbok.reset_config()


def test_format_context():
    context = {
        'my_number': 42,
        'my_func': lambda x: x,
    }
    result = arbok.format_context(context)
    assert result == '\n'.join([
        '{0}: {1!r}'.format(key, value)
        for key, value in context.items()
    ])


def test_default_make_banner():
    result = arbok.make_banner()
    assert sys.version in result
    assert arbok.DEFAULT_BANNER_TEXT in result


def test_make_banner_custom():
    text = 'I want to be the very best'
    result = arbok.make_banner(text)
    assert text in result
    assert sys.version in result


def test_make_banner_with_context():
    context = {'foo': 42}
    result = arbok.make_banner(context=context)
    assert arbok.format_context(context) in result


def test_cfg_defaults():
    assert arbok.DEFAULT_OPTIONS['shell'] == arbok.AutoShell
    assert arbok.DEFAULT_OPTIONS['banner'] == arbok.DEFAULT_BANNER_TEXT
    assert arbok.DEFAULT_OPTIONS['context'] == {}


def test_config():
    assert arbok.cfg == arbok.DEFAULT_OPTIONS
    arbok.config({
        'banner': 'Foo bar'
    })
    assert arbok.cfg['banner'] == 'Foo bar'


def test_reset_config():
    assert arbok.cfg == arbok.DEFAULT_OPTIONS
    arbok.config({
        'banner': 'Foo bar'
    })
    arbok.reset_config()
    assert arbok.cfg == arbok.DEFAULT_OPTIONS
