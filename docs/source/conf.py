import sphinx_rtd_theme
import sphinx_intl


project = "OnionShare"
author = (
    copyright
) = "Micah Lee, et al. Like all software, OnionShare may contain bugs or vulnerabilities."
version = release = "2.3"

extensions = ["sphinx_rtd_theme"]
templates_path = ["_templates"]
exclude_patterns = []

html_theme = "sphinx_rtd_theme"
html_logo = "_static/logo.png"
html_favicon = "_static/favicon.ico"
html_theme_options = {}
html_static_path = ["_static"]
html_css_files = ["custom.css"]
html_show_sourcelink = False
html_show_sphinx = False

# sphinx-intl
language = "en"
locale_dirs = ["locale/"]
gettext_compact = False
