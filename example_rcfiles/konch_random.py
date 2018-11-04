# -*- coding: utf-8 -*-
# vi: set ft=python :

import random

import konch

banner = """
"Probability is not a mere computation of odds on the dice or more complicated
variants; it is the acceptance of the lack of certainty in our knowledge and
the development of methods for dealing with our ignorance."
- Nassim Nickolas Taleb
"""

konch.config(
    {
        "context": [random.randint, random.random, random.choice],
        "banner": banner,
        "shell": konch.IPythonShell,
    }
)
