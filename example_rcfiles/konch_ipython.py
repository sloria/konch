import datetime

import konch
import pandas
import numpy

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
