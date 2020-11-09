import sphinx_rtd_theme
import sphinx_intl


project = "OnionShare"
author = copyright = "Micah Lee, et al."
version = release = "2.3"

extensions = ["sphinx_rtd_theme"]
templates_path = ["_templates"]
exclude_patterns = []

languages = [
    ("Español", "es"),
    ("English", "en"),
    ("Українська", "uk"),
]

versions = ["2.3.dev2"]

html_theme = "sphinx_rtd_theme"
html_logo = "_static/logo.png"
html_favicon = "_static/favicon.ico"
html_theme_options = {}
html_context = {"langs": languages, "versions": versions, "current_version": release}
html_static_path = ["_static"]
html_css_files = ["custom.css"]
html_show_sourcelink = False
html_show_sphinx = False

# sphinx-intl
language = "en"
locale_dirs = ["locale/"]
gettext_compact = False
