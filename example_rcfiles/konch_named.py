# -*- coding: utf-8 -*-
# vi: set ft=python :
"""Example .konchrc with named configs.

To use a named config, run:

    $ konch --name=trig

or

    $ konch -n trig
"""
import os
import sys
import math


import konch

# the default config
konch.config({
    'context': [os, sys],
    'banner': 'The default shell'
})

# A named config
konch.named_config('trig', {
    'context': [math.sin, math.tan, math.cos],
    'banner': 'The trig shell'
})

konch.named_config('func', {
    'context': [math.gamma, math.exp, math.log],
    'banner': 'The func shell'
})
