#!/usr/bin/env python
# -*- coding: utf-8 -*-
import flask

import arbok

arbok.config({
    'context': {
        'request': flask.request,
        'url_for': flask.url_for,
        'Flask': flask.Flask,
        'render_template': flask.render_template
    }
})
