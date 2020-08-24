import sphinx_rtd_theme
import sphinx_intl


project = "OnionShare"
author = copyright = "Micah Lee, et al."
version = release = "2.3"

extensions = ["sphinx_rtd_theme"]

templates_path = ["_templates"]

exclude_patterns = []

html_theme = "sphinx_rtd_theme"
html_logo = "_static/logo.svg"
html_theme_options = {}
html_static_path = ["_static"]

# sphinx-intl
locale_dirs = ["locale/"]
gettext_compact = False
