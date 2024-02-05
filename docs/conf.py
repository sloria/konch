import importlib.metadata
import os
import sys

sys.path.append(os.path.abspath("_themes"))

# -- General configuration -----------------------------------------------------

extensions = ["sphinx.ext.autodoc", "sphinx_issues"]

issues_github_path = "sloria/doitlive"

templates_path = ["_templates"]

source_suffix = ".rst"
master_doc = "index"

project = "konch"

version = release = importlib.metadata.version("konch")

exclude_patterns = ["_build"]

pygments_style = "flask_theme_support.FlaskyStyle"

html_theme = "kr_small"

# Theme options are theme-specific and customize the look and feel of a theme
# further.  For a list of options available for each theme, see the
# documentation.
html_theme_options = {
    "index_logo": "konch.png",
    "index_logo_height": "200px",
    "github_fork": "sloria/konch",
}

# Add any paths that contain custom themes here, relative to this directory.
html_theme_path = ["_themes"]

html_sidebars = {
    "index": ["side-primary.html", "searchbox.html"],
    "**": ["side-secondary.html", "localtoc.html", "relations.html", "searchbox.html"],
}
