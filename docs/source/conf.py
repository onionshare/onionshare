project = "OnionShare"
author = copyright = "Micah Lee, et al."
version = release = "2.6"

extensions = ["sphinx_rtd_theme"]
templates_path = ["_templates"]
exclude_patterns = []

languages = [
    ("English", "en"),  # English
    ("Français", "fr"),  # French
    ("Deutsch", "de"),  # German
    ("Ελληνικά", "el"),  # Greek
    ("Italiano", "it"),  # Italian
    ("Norsk Bokmål", "nb_NO"),  # Norwegian Bokmål
    ("Polish", "pl"),  # Polish
    ("Portuguese (Brazil)", "pt_BR"),  # Portuguese (Brazil))
    ("Русский", "ru"),  # Russian
    ("Español", "es"),  # Spanish
    ("Türkçe", "tr"),  # Turkish
    ("Українська", "uk"),  # Ukrainian
]

versions = ["2.3", "2.3.1", "2.3.2", "2.3.3", "2.4", "2.5", "2.6"]

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
