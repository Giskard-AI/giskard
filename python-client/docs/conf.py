# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'giskard'
copyright = '2023, Giskard AI'
author = 'Giskard AI'
release = '1.8.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ["myst_parser", 'sphinx.ext.todo', 'sphinx.ext.viewcode', 'sphinx_rtd_theme',
              'sphinx.ext.napoleon', 'sphinx.ext.autodoc']

autodoc_mock_imports = ["giskard.ml_worker.generated"]
templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'furo'
# html_static_path = ['_static']

import os
import sys

sys.path.insert(0, os.path.abspath('../'))
