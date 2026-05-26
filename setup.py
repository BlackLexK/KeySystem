#!/usr/bin/env python3
"""
KeyControlApp — Информационная система учёта выдачи и возврата ключей.
"""

from setuptools import setup, find_packages

# Чтение requirements.txt с fallback на разные кодировки
try:
    with open("requirements.txt", "r", encoding="utf-8") as fh:
        requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]
except UnicodeDecodeError:
    with open("requirements.txt", "r", encoding="utf-8-sig") as fh:
        requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="key-control-app",
    version="1.0.0",
    author="----",
    author_email="----",
    description="ИС учёта выдачи и возврата ключей",
    long_description="Информационная система для автоматизации учёта выдачи и возврата ключей.",
    long_description_content_type="text/plain",
    url="----",
    py_modules=["main", "auth", "gui", "models", "services", "database", "utils"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Education",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "keycontrol=main:start_app",
        ],
    },
)
