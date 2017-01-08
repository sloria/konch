# -*- coding: utf-8 -*-
import datetime as dt
import sys
import os

sys.path.insert(0, os.path.abspath('..'))
import konch
sys.path.append(os.path.abspath("_themes"))

# -- General configuration -----------------------------------------------------

extensions = ['sphinx.ext.autodoc']

templates_path = ['_templates']

source_suffix = '.rst'
master_doc = 'index'

project = u'konch'
copyright = u'2014-{0:%Y}'.format(dt.datetime.utcnow())

version = release = konch.__version__

exclude_patterns = ['_build']

pygments_style = 'flask_theme_support.FlaskyStyle'

html_theme = 'kr_small'

# Theme options are theme-specific and customize the look and feel of a theme
# further.  For a list of options available for each theme, see the
# documentation.
html_theme_options = {
    'index_logo': 'konch.png',
    'index_logo_height': '200px',
    'github_fork': 'sloria/konch'
}

# Add any paths that contain custom themes here, relative to this directory.
html_theme_path = ['_themes']

html_sidebars = {
    'index': ['side-primary.html', 'searchbox.html'],
    '**': ['side-secondary.html', 'localtoc.html',
                 'relations.html', 'searchbox.html']
}

latex_documents = [
    ('index', 'konch.tex', u'konch Documentation',
    u'Steven Loria', 'manual'),
]
man_pages = [
    ('index', 'konch', u'konch Documentation',
     [u'Steven Loria'], 1)
]

texinfo_documents = [
    ('index', 'konch', u'konch Documentation',
    u'Steven Loria', 'konch', 'HTTP Request Parsing for Pirates',
    ''),
]
