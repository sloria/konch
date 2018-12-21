# -*- coding: utf-8 -*-
import re
from setuptools import setup


EXTRAS_REQUIRE = {
    "tests": ["pytest", "mock", "scripttest==1.3", "ipython", "bpython", "ptpython"],
    "lint": [
        "flake8==3.6.0",
        'flake8-bugbear==18.8.0; python_version >= "3.5"',
        "pre-commit==1.13.0",
    ],
    "docs": ["sphinx"],
}
EXTRAS_REQUIRE["dev"] = (
    EXTRAS_REQUIRE["tests"] + EXTRAS_REQUIRE["lint"] + EXTRAS_REQUIRE["docs"] + ["tox"]
)


def find_version(fname):
    """Attempts to find the version number in the file names fname.
    Raises RuntimeError if not found.
    """
    version = ""
    with open(fname, "r") as fp:
        reg = re.compile(r'__version__ = [\'"]([^\'"]*)[\'"]')
        for line in fp:
            m = reg.match(line)
            if m:
                version = m.group(1)
                break
    if not version:
        raise RuntimeError("Cannot find version information")
    return version


def read(fname):
    with open(fname) as fp:
        content = fp.read()
    return content


setup(
    name="konch",
    version=find_version("konch.py"),
    description=(
        "CLI and configuration utility for the Python shell, optimized "
        "for simplicity and productivity."
    ),
    long_description=(read("README.rst") + "\n\n" + read("CHANGELOG.rst")),
    author="Steven Loria",
    author_email="sloria1@gmail.com",
    url="https://github.com/sloria/konch",
    install_requires=[],
    extras_require=EXTRAS_REQUIRE,
    license="MIT",
    zip_safe=False,
    keywords="konch shell custom ipython bpython repl ptpython ptipython",
    classifiers=[
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Topic :: System :: Shells",
    ],
    py_modules=["konch", "docopt"],
    entry_points={"console_scripts": ["konch = konch:main"]},
)
