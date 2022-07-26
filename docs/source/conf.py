# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

autodoc_mock_imports = ["enum_tools"]
autodoc_mock_imports = ["sphinxcontrib-bibtex"]


# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
# import os
# import sys
# sys.path.insert(0, os.path.abspath('.'))
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join('.', '..', 'src')))
sys.path.insert(0, os.path.abspath('.'))
sys.path.append(os.path.abspath('..'))


sys.path.append(os.path.abspath('../datastructs'))
sys.path.append(os.path.abspath('../automation'))
sys.path.append(os.path.abspath('../bottomup'))
sys.path.append(os.path.abspath('../core'))
sys.path.append(os.path.abspath('../misc'))

# -- Project information -----------------------------------------------------

project = 'sfctools'
copyright = '2021-2022, German Aerospace Center (DLR)'
author = 'Thomas Baldauf'

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.

extensions = ['sphinx.ext.autodoc',
'sphinx.ext.napoleon',
"sphinx_rtd_theme",
"enum_tools.autoenum",
'sphinxcontrib.bibtex']

bibtex_encoding = 'latin'
bibtex_default_style = 'unsrt'
bibtex_reference_style  = 'author_year'
bibtex_bibfiles = ['literature_architecture.bib']


# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []

autoclass_content = 'both'

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'sphinx_rtd_theme'
html_theme_options = {
    # "rightsidebar": "true",
    #"relbarbgcolor": "black",
    "globaltoc_includehidden":"true"
}
# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = [] # '_static']
