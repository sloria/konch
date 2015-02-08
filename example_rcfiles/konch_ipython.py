# -*- coding: utf-8 -*-
import datetime as dt

import konch
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

konch.config({
    'context': {
        'dt': dt,
        'pd': pd,
        'plt': plt,
        'np': np,
    },
    'shell': 'ipython',
    'ipy_autoreload': True,
    'ipy_extensions': [
        # Ipython extensions here
    ]
})
