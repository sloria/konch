import re
from setuptools import setup, Command


EXTRAS_REQUIRE = {
    "tests": ["pytest", "mock", "scripttest==1.3", "ipython", "bpython"],
    "lint": [
        "mypy==0.790",
        "flake8==3.8.4",
        "flake8-bugbear==20.11.1",
        "pre-commit~=2.3",
    ],
}
EXTRAS_REQUIRE["dev"] = (
    EXTRAS_REQUIRE["tests"] + EXTRAS_REQUIRE["lint"] + ["ptpython", "tox"]
)
PYTHON_REQUIRES = ">=3.6"


class Shell(Command):
    user_options = [
        ("name=", "n", "Named config to use."),
        ("shell=", "s", "Shell to use."),
        ("file=", "f", "File path of konch config file to execute."),
    ]

    def initialize_options(self):
        self.name = None
        self.shell = None
        self.file = None

    def finalize_options(self):
        pass

    def run(self):
        import konch

        argv = []
        for each in ("name", "shell", "file"):
            opt = getattr(self, each)
            if opt:
                argv.append(f"--{each}={opt}")
        konch.main(argv)


def find_version(fname):
    """Attempts to find the version number in the file names fname.
    Raises RuntimeError if not found.
    """
    version = ""
    with open(fname) as fp:
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
    long_description=read("README.rst"),
    author="Steven Loria",
    author_email="sloria1@gmail.com",
    url="https://github.com/sloria/konch",
    install_requires=[],
    cmdclass={"shell": Shell},
    extras_require=EXTRAS_REQUIRE,
    python_requires=PYTHON_REQUIRES,
    license="MIT",
    zip_safe=False,
    keywords="konch shell custom ipython bpython repl ptpython ptipython",
    classifiers=[
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Topic :: System :: Shells",
    ],
    py_modules=["konch", "docopt"],
    entry_points={"console_scripts": ["konch = konch:main"]},
    project_urls={
        "Changelog": "https://konch.readthedocs.io/en/latest/changelog.html",
        "Issues": "https://github.com/sloria/konch/issues",
        "Source": "https://github.com/sloria/konch/",
    },
)
