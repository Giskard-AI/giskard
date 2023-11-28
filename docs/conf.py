import inspect
import os
import sys

# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "Giskard"
copyright = "2023, Giskard AI"
author = "Giskard AI"
release = "2.0.0"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "myst_parser",
    "nbsphinx",
    "sphinx_design",
    "sphinx.ext.todo",
    "sphinx.ext.napoleon",
    "sphinx.ext.autodoc",
    "sphinx.ext.linkcode",
    "sphinx_tabs.tabs",
    "sphinx_copybutton",
    "sphinx_tabs.tabs",
    "sphinx_click",
]

autoclass_content = "both"

# autodoc_mock_imports = ["giskard.ml_worker.generated"]
templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

myst_enable_extensions = [
    "amsmath",
    "attrs_inline",
    "colon_fence",
    "deflist",
    "dollarmath",
    "fieldlist",
    "html_admonition",
    "html_image",
    "replacements",
    "smartquotes",
    "strikethrough",
    "substitution",
    "tasklist",
]

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

# -----------------------------------------------------------------------------
# HTML output
# -----------------------------------------------------------------------------

html_title = "Giskard Documentation"
html_favicon = "favicon.ico"

html_theme = "furo"
html_static_path = ["_static"]

html_css_files = ["css/custom.css"]
html_js_files = ["js/githubStargazers.js", "js/sidebarKeepScroll.js", "js/reodev.js"]

html_theme_options = {
    "light_logo": "logo_black.png",
    "dark_logo": "logo_white.png",
    "light_css_variables": {
        "color-brand-content": "#173A2F",
        "color-api-highlight": "#56D793",
        "color-api-background": "#F5F5F5",
        "color-toc-item-text--active": "#56D793",
        "color-sidebar-current-text": "#56D793",
        "color-sidebar-link-text--top-level": "#0c0c0c",
        "color-content-foreground": "#484848",
        "social-button-background": "#FFFFFF",
        "social-button-text": "#91F6C0",
    },
    "dark_css_variables": {
        "color-brand-primary": "#56D793",
        "color-brand-content": "#91F6C0",
        "color-api-background": "#242424",
        "color-sidebar-current-text": "#56D793",
        "color-toc-title": "#C4C4C4",
        "color-toc-item-text--active": "#56D793",
        "color-sidebar-link-text--top-level": "#FcFcFc",
        "color-sidebar-search-foreground": "#a4a4a4",
        "color-sidebar-search-border": "#a4a4a4",
        "color-content-foreground": "#FFFFFF",
        "social-button-background": "#000000",
        "social-button-text": "#000000",
    },
    "sidebar_hide_name": False,
    "navigation_with_keys": True,
    "top_of_page_button": "edit",
    "source_repository": "https://github.com/Giskard-AI/giskard",
    "source_branch": "main",
    "source_directory": "docs/",
    "source_edit_link": "https://github.com/Giskard-AI/giskard/edit/main/docs/{filename}",
}

add_function_parentheses = False
# Do not execute the notebooks when building the docs
docs_version = os.getenv("READTHEDOCS_VERSION", "latest")
if docs_version == "latest":
    branch = "main"
else:
    branch = docs_version.replace("-", "/")

nbsphinx_execute = "never"
# fmt: off
nbsphinx_prolog = """
.. raw:: html

    <div class="open-in-colab__wrapper">
    <a href="https://colab.research.google.com/github/giskard-ai/giskard/blob/""" + branch + """/docs/{{ env.doc2path(env.docname, base=None) }}" target="_blank"><img src="https://colab.research.google.com/assets/colab-badge.svg" style="display: inline; margin: 0" alt="Open In Colab"/></a>
    <a href="https://github.com/giskard-ai/giskard/tree/""" + branch + """/docs/{{ env.doc2path(env.docname, base=None) }}" target="_blank"><img src="https://img.shields.io/badge/github-view%20source-black.svg" style="display: inline; margin: 0" alt="View Notebook on GitHub"/></a>
    </div>
"""
# fmt: on

sys.path.insert(0, os.path.abspath("../"))

pygments_style = "github-dark"
pygments_dark_style = "material"


# make github links resolve
def linkcode_resolve(domain, info):
    if domain != "py":
        return None

    modname = info["module"]
    fullname = info["fullname"]
    print("##############")
    print(f"modname:{modname}")
    print(f"fullname:{fullname}")

    submod = sys.modules.get(modname)
    # print(submod)
    if submod is None:
        print("##############")

        return None
    obj = submod
    for part in fullname.split("."):
        try:
            obj = getattr(obj, part)
            print(f"obj:{obj}")

            # print(obj)
        except:  # noqa: E722
            print("##############")
            return None

    try:
        fn = inspect.getsourcefile(
            obj.test_fn if hasattr(obj, "test_fn") else obj
        )  # TODO: generalise for other objects!
    # print(fn)
    except:  # noqa: E722
        fn = None
    if not fn:
        print("##############")

        return None
    print(f"fn:{fn}")

    try:
        source, lineno = inspect.getsourcelines(obj)
    except:  # noqa: E722
        lineno = None

    if lineno:
        linespec = "#L%d-L%d" % (lineno, lineno + len(source) - 1)
    else:
        linespec = ""
    print(f"linespec:{linespec}")

    filename = fn.split("giskard")[-1]
    print("##############")

    return f"https://github.com/Giskard-AI/giskard/blob/main/giskard{filename}{linespec}"
