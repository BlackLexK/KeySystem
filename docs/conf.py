"""
Конфигурация Sphinx для документации KeyControlApp.
"""

import os
import sys

# Добавляем родительскую директорию в путь для импорта модулей
sys.path.insert(0, os.path.abspath('..'))

# -- Основная информация о проекте ------------------------------------

project = 'KeyControlApp'
copyright = '----'
author = '----'
release = '1.0.0'

# -- Общие настройки --------------------------------------------------

extensions = [
    'sphinx.ext.autodoc',      # Автоматическая документация из docstrings
    'sphinx.ext.napoleon',     # Поддержка Google и NumPy style docstrings
    'sphinx.ext.viewcode',     # Ссылки на исходный код
    'sphinx.ext.todo',         # Поддержка TODO
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# -- Настройки HTML ---------------------------------------------------

html_theme = 'alabaster'

# -- Настройки autodoc ------------------------------------------------

autodoc_member_order = 'bysource'
autodoc_default_options = {
    'members': True,
    'member-order': 'bysource',
    'special-members': '__init__',
    'undoc-members': True,
    'exclude-members': '__weakref__'
}

# -- Настройки Napoleon -----------------------------------------------

napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = True
napoleon_use_admonition_for_notes = True
napoleon_use_param = True
napoleon_use_rtype = True
