# -*- coding: utf-8 -*-
import konch
import requests

konch.config({
    'context': {
        'httpget': requests.get,
        'httppost': requests.post,
        'httpput': requests.put,
        'httpdelete': requests.delete
    },
    'banner': 'A humanistic HTTP shell'
})
