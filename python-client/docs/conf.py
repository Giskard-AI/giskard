# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'giskard'
copyright = '2023, Giskard AI'
author = 'Giskard AI'
release = '2.0.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ["myst_parser",
              'sphinx.ext.todo',
              'sphinx_rtd_theme',  # 'sphinx.ext.viewcode',
              'sphinx.ext.napoleon',
              'sphinx.ext.autodoc',
              'sphinx.ext.linkcode']

autodoc_mock_imports = ["giskard.ml_worker.generated"]
templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'furo'
# html_static_path = ['_static']

import os
import sys
import inspect

sys.path.insert(0, os.path.abspath('../'))


# make github links resolve
def linkcode_resolve(domain, info):
    if domain != "py":
        return None

    modname = info["module"]
    fullname = info["fullname"]

    submod = sys.modules.get(modname)
    print(submod)
    if submod is None:
        return None

    for part in fullname.split("."):
        try:
            obj = getattr(submod, part)
            print(obj)
        except:  # noqa: E722
            return None

    try:
        fn = inspect.getsourcefile(obj.test_fn)  # TODO: generalise for other objects!
        print(fn)
    except:  # noqa: E722
        fn = None
    if not fn:
        return None

    try:
        source, lineno = inspect.getsourcelines(obj)
    except:  # noqa: E722
        lineno = None

    if lineno:
        linespec = "#L%d-L%d" % (lineno, lineno + len(source) - 1)
    else:
        linespec = ""

    filename = fn.split("python-client", 1)[-1]
    return f"https://github.com/Giskard-AI/giskard/blob/feature/ai-test-v2-merged/python-client{filename}{linespec}"
