#!/usr/bin/env python
# -*- coding: utf-8 -*-
import flask

import konch

konch.config({
    'context': {
        'request': flask.request,
        'url_for': flask.url_for,
        'Flask': flask.Flask,
        'render_template': flask.render_template
    }
})
