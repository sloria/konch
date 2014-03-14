#!/usr/bin/env python
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
