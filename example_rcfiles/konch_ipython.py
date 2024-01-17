import datetime

import numpy
import pandas

import konch

konch.config(
    {
        "context": [datetime, pandas, numpy],
        "shell": "ipython",
        "ipy_autoreload": True,
        "ipy_extensions": [
            # Ipython extensions here
        ],
    }
)
